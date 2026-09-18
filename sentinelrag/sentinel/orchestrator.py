from __future__ import annotations

import os
import uuid
from datetime import date
from typing import Optional

from .agent_loop import AgentLoop
from .answer_synthesis import AnswerSynthesisAgent
from .audit import AuditLog
from .authorization import AuthorizationGatekeeper
from .conflict_resolver import ConflictResolver
from .document_store import DocumentStore
from .llm_client import LLMClient
from .models import User
from .query_planner import QueryPlanningAgent
from .retrieval import RetrievalAgent


class SentinelRAGPipeline:
    """Two paths, one identical response shape.

    When an LLM is configured, the agentic tool-calling loop (AgentLoop)
    decides how to search; when it isn't, a fixed deterministic sequence
    runs instead. Both return the exact same response shape (query_id,
    answer, citations, evidence_firewall, conflicts, llm_mode), so the
    API, the CLI, and the tests never need to know which path executed.

    Neither path can skip authorization: the deterministic path always
    runs the Authorization Gatekeeper immediately after retrieval, and
    the agentic path fuses retrieval + authorization inside
    DocumentSearchTool, the only tool the LLM can call.

    Set AGENTIC_MODE=false to force the deterministic path even with an
    LLM configured -- a safety switch for a live demo if the agent loop
    ever needs to be ruled out as the source of a problem.
    """

    def __init__(self, document_store: DocumentStore, audit_log: Optional[AuditLog] = None) -> None:
        self.document_store = document_store
        self.retrieval = RetrievalAgent()
        self.gatekeeper = AuthorizationGatekeeper()
        self.conflict_resolver = ConflictResolver()
        self.llm_client = LLMClient()
        self.query_planner = QueryPlanningAgent(self.llm_client)
        self.answer_agent = AnswerSynthesisAgent(self.llm_client)
        self.agent_loop = AgentLoop(self.llm_client)
        self.audit = audit_log or AuditLog()
        self._agentic_enabled = os.getenv("AGENTIC_MODE", "true").strip().lower() != "false"

    def run(self, user: User, question: str, today: Optional[date] = None) -> dict:
        query_id = str(uuid.uuid4())[:8]
        self.audit.log_query(query_id, user.user_id, question)

        if self.llm_client.enabled and self._agentic_enabled:
            result = self._run_agentic(user, question, today)
        else:
            result = self._run_deterministic(user, question, today)

        stats = result["evidence_firewall"]
        if result.get("decisions") is not None:
            self.audit.log_decisions(query_id, result["decisions"])
        if result.get("tool_calls"):
            self.audit.log_tool_calls(query_id, result["tool_calls"])
        self.audit.log_evidence(query_id, result["resolved_documents"])
        self.audit.log_answer(query_id, result["answer"], stats["retrieved"], stats["authorized"], stats["blocked"])

        return {
            "query_id": query_id,
            "answer": result["answer"],
            "citations": result["citations"],
            "evidence_firewall": stats,
            "conflicts": result["conflicts"],
            "llm_mode": self.llm_client.provider if self.llm_client.enabled else "stub",
        }

    def _run_deterministic(self, user: User, question: str, today: Optional[date]) -> dict:
        search_query = self.query_planner.plan(question)

        all_docs = self.document_store.all()
        scored = self.retrieval.search(search_query, all_docs)
        candidates = [doc for doc, _score in scored]

        allowed_docs, decisions = self.gatekeeper.filter(user, candidates, today)

        resolved = self.conflict_resolver.resolve(allowed_docs, today)
        superseded = self.conflict_resolver.last_superseded

        answer = self.answer_agent.answer(question, resolved, superseded)

        retrieved_count = len(candidates)
        authorized_count = len(allowed_docs)
        blocked_count = retrieved_count - authorized_count

        return {
            "answer": answer,
            "citations": [
                {
                    "document_id": d.document_id,
                    "title": d.title,
                    "version": d.version,
                    "classification": d.classification,
                }
                for d in resolved
            ],
            "evidence_firewall": {
                "retrieved": retrieved_count,
                "authorized": authorized_count,
                "blocked": blocked_count,
            },
            "conflicts": [c.title for c in self.conflict_resolver.last_conflicts],
            "decisions": decisions,
            "resolved_documents": resolved,
        }

    def _run_agentic(self, user: User, question: str, today: Optional[date]) -> dict:
        all_docs = self.document_store.all()
        return self.agent_loop.run(user, question, all_docs, today)
