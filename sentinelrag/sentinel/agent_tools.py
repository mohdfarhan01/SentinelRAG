from __future__ import annotations

from datetime import date
from typing import List, Optional

from .authorization import AuthorizationGatekeeper
from .conflict_resolver import ConflictResolver
from .models import Document, User
from .retrieval import RetrievalAgent

# OpenAI-compatible function-calling schema for providers (like DeepSeek via
# chat.b.ai) that need an explicit JSON schema rather than introspecting a
# Python callable. Google Gemini's automatic function calling introspects
# the DocumentSearchTool.as_callable() function directly instead and does
# not need this, but both paths call the exact same underlying tool.
SEARCH_DOCUMENTS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "Search the enterprise document store for content relevant to "
            "a query. Authorization is enforced automatically -- this "
            "only ever returns documents the current employee is allowed "
            "to see. If other relevant documents exist but are blocked, "
            "you are told how many, never their titles or content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms, or a reformulated version of the employee's question.",
                }
            },
            "required": ["query"],
        },
    },
}


class DocumentSearchTool:
    """The ONE retrieval tool exposed to the LLM.

    Retrieval and authorization are fused here, unconditionally: every
    call runs RetrievalAgent -> AuthorizationGatekeeper -> ConflictResolver
    in that fixed order before anything is returned. There is no separate
    "retrieve" tool the model could call to get unfiltered content, and no
    parameter through which the model can specify whose permissions to
    search with -- `user` is bound once, at construction, from the
    server's own authenticated request context.

    Also self-limits the number of real searches it will perform per
    request, independent of whatever looping behavior a given LLM
    provider implements -- so the cap holds even if a provider's own tool
    loop has a bug or a generous default.
    """

    def __init__(
        self,
        user: User,
        all_documents: List[Document],
        today: Optional[date] = None,
        max_calls: int = 3,
    ) -> None:
        self._user = user
        self._all_documents = all_documents
        self._today = today
        self._max_calls = max_calls
        self._total_calls = 0

        self.retrieval = RetrievalAgent()
        self.gatekeeper = AuthorizationGatekeeper()
        self.conflict_resolver = ConflictResolver()
        self.call_log: List[dict] = []

    def as_callable(self):
        """Returns a plain function (not a bound method) wrapping this
        tool, with a clean signature and docstring for providers that
        introspect a Python callable to build a schema (Gemini's
        automatic function calling). A bound method's introspected
        signature/doc can behave inconsistently across SDKs, so this
        closure is deliberately a plain top-level-shaped function."""

        def search_documents(query: str) -> str:
            """Search the enterprise document store for content relevant
            to a query. Authorization is enforced automatically. Call
            this to find evidence for the employee's question; you may
            call it again with a reformulated query if the first search
            wasn't sufficient, up to a limit.

            Args:
                query: search terms, or a reformulated version of the question
            """
            return self.run(query)

        return search_documents

    def run(self, query: str) -> str:
        self._total_calls += 1
        if self._total_calls > self._max_calls:
            return (
                f"Search limit reached ({self._max_calls} searches for this "
                "request). Do not call search_documents again -- answer now "
                "using only the evidence already gathered above."
            )

        candidates = [doc for doc, _score in self.retrieval.search(query, self._all_documents)]
        allowed_docs, decisions = self.gatekeeper.filter(self._user, candidates, self._today)
        resolved = self.conflict_resolver.resolve(allowed_docs, self._today)
        superseded = self.conflict_resolver.last_superseded

        retrieved_count = len(candidates)
        authorized_count = len(allowed_docs)
        blocked_count = retrieved_count - authorized_count

        self.call_log.append(
            {
                "query": query,
                "retrieved": retrieved_count,
                "authorized": authorized_count,
                "blocked": blocked_count,
                "decisions": decisions,
                "resolved_documents": resolved,
                "superseded_documents": superseded,
            }
        )

        return self._format_result(resolved, superseded, blocked_count)

    def _format_result(
        self, resolved: List[Document], superseded: List[Document], blocked_count: int
    ) -> str:
        if not resolved:
            note = (
                f" ({blocked_count} relevant document(s) were found but you are "
                "not authorized to access them.)"
                if blocked_count
                else ""
            )
            return f"No authorized evidence found for this query.{note}"

        parts = [
            f"[{d.document_id} | {d.title} v{d.version} | effective {d.effective_date}]\n{d.content}"
            for d in resolved
        ]
        block = "\n\n".join(parts)

        if superseded:
            block += "\n\nSuperseded documents (context only, do not cite as current): " + ", ".join(
                f"{d.document_id} ({d.effective_date})" for d in superseded
            )

        if blocked_count:
            block += (
                f"\n\n({blocked_count} additional relevant document(s) were found "
                "but you are not authorized to access them -- do not speculate "
                "about their content.)"
            )

        return block
