from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

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
    """Wires every agent together in one fixed order. Retrieval always
    finds candidates from the WHOLE store; the Authorization Gatekeeper
    always runs immediately after, before anything else can touch the
    candidates' content. There is no code path that skips it.
    """

    def __init__(self, document_store: DocumentStore, audit_log: Optional[AuditLog] = None) -> None:
        self.document_store = document_store
        self.retrieval = RetrievalAgent()
        self.gatekeeper = AuthorizationGatekeeper()
        self.conflict_resolver = ConflictResolver()
        self.llm_client = LLMClient()
        self.query_planner = QueryPlanningAgent(self.llm_client)
        self.answer_agent = AnswerSynthesisAgent(self.llm_client)
        self.audit = audit_log or AuditLog()

    def run(self, user: User, question: str, today: Optional[date] = None) -> dict:
        query_id = str(uuid.uuid4())[:8]
        self.audit.log_query(query_id, user.user_id, question)

        search_query = self.query_planner.plan(question)

        all_docs = self.document_store.all()
        scored = self.retrieval.search(search_query, all_docs)
        candidates = [doc for doc, _score in scored]

        allowed_docs, decisions = self.gatekeeper.filter(user, candidates, today)
        self.audit.log_decisions(query_id, decisions)

        resolved = self.conflict_resolver.resolve(allowed_docs, today)
        superseded = self.conflict_resolver.last_superseded
        self.audit.log_evidence(query_id, resolved)

        answer = self.answer_agent.answer(question, resolved, superseded)

        retrieved_count = len(candidates)
        authorized_count = len(allowed_docs)
        blocked_count = retrieved_count - authorized_count
        self.audit.log_answer(query_id, answer, retrieved_count, authorized_count, blocked_count)

        return {
            "query_id": query_id,
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
            "llm_mode": self.llm_client.provider if self.llm_client.enabled else "stub",
        }
