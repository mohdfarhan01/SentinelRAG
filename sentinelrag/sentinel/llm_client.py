from __future__ import annotations

import json
import os
import time

import requests


class LLMClient:
    """One swappable seam for the entire codebase.

    Defaults to a disabled STUB mode that requires no API key and makes no
    network calls, so every other agent works and is testable without one.

    Provider selection:
      - LLM_PROVIDER=gemini   -> Google Gemini (GEMINI_API_KEY, GEMINI_MODEL)
      - LLM_PROVIDER=deepseek -> DeepSeek via chat.b.ai (BAI_API_KEY, BAI_MODEL)
      - unset -> auto-detect: deepseek if BAI_API_KEY is set, else gemini
        if GEMINI_API_KEY is set, else disabled (STUB mode)

    Nothing outside this file should know or care which provider is
    active -- every caller only ever uses `.enabled` and `.generate(...)`.
    """

    def __init__(self) -> None:
        provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        bai_key = os.getenv("BAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        if not provider:
            if bai_key:
                provider = "deepseek"
            elif gemini_key:
                provider = "gemini"

        self.provider = provider or "stub"

        self._gemini_client = None
        self._gemini_model = None
        self._bai_key = None
        self._bai_base_url = None
        self._bai_model = None

        if self.provider == "gemini" and gemini_key:
            try:
                from google import genai

                self._gemini_client = genai.Client(api_key=gemini_key)
                self._gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
            except ImportError:
                self._gemini_client = None

        elif self.provider == "deepseek" and bai_key:
            self._bai_key = bai_key
            self._bai_base_url = os.getenv("BAI_BASE_URL", "https://api.b.ai/v1")
            self._bai_model = os.getenv("BAI_MODEL", "deepseek-v4-flash")

    @property
    def enabled(self) -> bool:
        return self._gemini_client is not None or self._bai_key is not None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self._gemini_client is not None:
            return self._generate_with_retry(self._generate_gemini, system_prompt, user_prompt)
        if self._bai_key is not None:
            return self._generate_with_retry(self._generate_bai, system_prompt, user_prompt)
        raise RuntimeError(
            "LLM not configured. Set GEMINI_API_KEY or BAI_API_KEY to enable "
            "real generation, or rely on the deterministic template answers "
            "used automatically in stub mode."
        )

    def _generate_with_retry(self, fn, system_prompt: str, user_prompt: str, attempts: int = 2) -> str:
        # Providers occasionally return transient 5xx errors under load.
        # One short retry avoids a demo query needlessly falling back to
        # the template answer over a passing blip. Callers still wrap
        # this in their own try/except for a final template fallback.
        last_error = None
        for attempt in range(attempts):
            try:
                return fn(system_prompt, user_prompt)
            except Exception as exc:  # noqa: BLE001 - deliberately broad, see above
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(1.5)
        raise last_error

    def _generate_gemini(self, system_prompt: str, user_prompt: str) -> str:
        from google.genai import types

        response = self._gemini_client.models.generate_content(
            model=self._gemini_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return (response.text or "").strip()

    def _generate_bai(self, system_prompt: str, user_prompt: str) -> str:
        resp = requests.post(
            f"{self._bai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._bai_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._bai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # This provider also returns a separate "reasoning_content" field
        # (the model's chain-of-thought) alongside "content" -- we only
        # want the final answer.
        return (data["choices"][0]["message"]["content"] or "").strip()

    def run_agent_loop(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_schema: dict,
        tool_callable,
        tool_fn,
        max_tool_calls: int = 3,
    ) -> str:
        """Runs a tool-calling loop where the model itself decides whether
        to call `search_documents` again or answer now, up to
        `max_tool_calls` rounds. `tool_callable` is a plain Python function
        (used by providers that introspect a callable to build a schema,
        e.g. Gemini's automatic function calling); `tool_fn` is the same
        underlying tool invoked manually (used by providers that need an
        explicit JSON schema and a hand-rolled loop, e.g. DeepSeek's
        OpenAI-compatible API). Both ultimately call the same
        DocumentSearchTool instance, so the security guarantee is
        identical regardless of which path executes.
        """
        if self._gemini_client is not None:
            return self._run_agent_loop_gemini(system_prompt, user_prompt, tool_callable, max_tool_calls)
        if self._bai_key is not None:
            return self._run_agent_loop_bai(system_prompt, user_prompt, tool_schema, tool_fn, max_tool_calls)
        raise RuntimeError("LLM not configured; run_agent_loop requires an active provider.")

    def _run_agent_loop_gemini(
        self, system_prompt: str, user_prompt: str, tool_callable, max_tool_calls: int, attempts: int = 2
    ) -> str:
        from google.genai import types

        # Gemini's automatic function calling runs its whole tool loop
        # inside this one SDK call, so a retry here re-invokes the tool
        # from scratch on failure -- unlike the DeepSeek path, there's no
        # way to retry just the network leg. This can add one or two
        # extra (still-capped, still-authorized) searches to the audit
        # trail on a retry; accepted as the simpler tradeoff against
        # falling straight through to the plain-concatenation fallback.
        last_error = None
        for attempt in range(attempts):
            try:
                response = self._gemini_client.models.generate_content(
                    model=self._gemini_model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=[tool_callable],
                    ),
                )
                return (response.text or "").strip()
            except Exception as exc:  # noqa: BLE001 - deliberately broad, see above
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(1.5)
        raise last_error

    def _run_agent_loop_bai(
        self, system_prompt: str, user_prompt: str, tool_schema: dict, tool_fn, max_tool_calls: int
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for round_num in range(max_tool_calls + 1):
            # On the final round, stop offering the tool at all, forcing
            # a text answer with whatever evidence has been gathered so
            # far -- this is what actually bounds the loop, independent
            # of whether the model would otherwise keep calling.
            offer_tool = round_num < max_tool_calls
            message = self._post_bai_completion(messages, tool_schema if offer_tool else None)

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                return (message.get("content") or "").strip()

            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": tool_calls,
                }
            )
            for call in tool_calls:
                args = json.loads(call["function"]["arguments"] or "{}")
                result = tool_fn(**args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": result,
                    }
                )

        return ""

    def _post_bai_completion(self, messages: list, tool_schema: dict | None, attempts: int = 2) -> dict:
        # Retried per-request, not around the whole loop: the loop already
        # executed and logged real tool calls in earlier rounds, so
        # retrying only the network call (not re-running search_documents)
        # is what avoids duplicate searches while still surviving a
        # transient blip in any single round.
        last_error = None
        for attempt in range(attempts):
            try:
                resp = requests.post(
                    f"{self._bai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._bai_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._bai_model,
                        "messages": messages,
                        **({"tools": [tool_schema], "tool_choice": "auto"} if tool_schema else {}),
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]
            except Exception as exc:  # noqa: BLE001 - deliberately broad, see above
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(1.5)
        raise last_error
