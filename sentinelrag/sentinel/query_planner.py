from __future__ import annotations

from .llm_client import LLMClient


class QueryPlanningAgent:
    """Turns the raw natural-language question into a search query.

    In stub mode (no LLM configured) it passes the question straight
    through -- retrieval works fine on raw text at this corpus size. When
    an LLM is available it extracts a short keyword query instead, which
    is the one genuinely agentic decision this agent makes: it adapts its
    own behavior based on whether a tool (the LLM) is actually available,
    rather than failing.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    def plan(self, question: str) -> str:
        if not self.llm.enabled:
            return question

        try:
            prompt = (
                "Extract the 3 to 6 most important search keywords from this "
                "employee question. Reply with only the keywords, space "
                f"separated, no punctuation.\n\nQuestion: {question}"
            )
            keywords = self.llm.generate("You are a search query extractor.", prompt)
            return keywords or question
        except Exception:
            # Never let a flaky LLM call block retrieval -- fall back to the
            # raw question, which is always a safe, working search input.
            return question
