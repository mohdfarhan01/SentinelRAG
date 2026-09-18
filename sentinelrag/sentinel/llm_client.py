from __future__ import annotations

import os


class LLMClient:
    """One swappable seam for the entire codebase.

    Defaults to a disabled STUB mode that requires no API key and makes no
    network calls, so every other agent can be built and tested first.
    Set GEMINI_API_KEY (and optionally GEMINI_MODEL) in the environment or
    a .env file to enable real generation -- nothing else in the codebase
    needs to change.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._model = None

        if self.api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.model_name)
            except ImportError:
                self._model = None

    @property
    def enabled(self) -> bool:
        return self._model is not None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._model:
            raise RuntimeError(
                "LLM not configured. Set GEMINI_API_KEY to enable real "
                "generation, or rely on the deterministic template answers "
                "used automatically in stub mode."
            )
        response = self._model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        return (response.text or "").strip()
