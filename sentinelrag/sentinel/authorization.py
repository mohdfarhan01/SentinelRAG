from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from .models import CLEARANCE_LEVELS, Document, User


@dataclass
class Decision:
    document_id: str
    allowed: bool
    reason: str

    @staticmethod
    def allow(document_id: str, reason: str = "authorized") -> "Decision":
        return Decision(document_id, True, reason)

    @staticmethod
    def deny(document_id: str, reason: str) -> "Decision":
        return Decision(document_id, False, reason)


class AuthorizationGatekeeper:
    """The Evidence Firewall's deterministic core.

    This is the ONLY component in the system allowed to decide whether a
    document's content may proceed further down the pipeline. It never
    calls an LLM, its decision is never overridden downstream, and it is
    the one piece of this codebase that must be exhaustively unit-tested.
    """

    def check_access(self, user: User, doc: Document, today: Optional[date] = None) -> Decision:
        today = today or date.today()

        if doc.status != "active":
            return Decision.deny(doc.document_id, f"document status is '{doc.status}', not active")

        if doc.effective_date_obj > today:
            return Decision.deny(doc.document_id, "document is not yet effective")

        if doc.classification not in CLEARANCE_LEVELS:
            return Decision.deny(doc.document_id, f"unknown classification '{doc.classification}'")

        user_level = CLEARANCE_LEVELS.get(user.clearance, -1)
        if CLEARANCE_LEVELS[doc.classification] > user_level:
            return Decision.deny(doc.document_id, "user clearance level insufficient")

        if doc.allowed_departments and user.department not in doc.allowed_departments:
            return Decision.deny(doc.document_id, "user department not permitted")

        if doc.allowed_roles and user.role not in doc.allowed_roles:
            return Decision.deny(doc.document_id, "user role not permitted")

        if doc.allowed_users and user.user_id not in doc.allowed_users:
            return Decision.deny(doc.document_id, "user not explicitly permitted")

        return Decision.allow(doc.document_id)

    def filter(
        self, user: User, documents: List[Document], today: Optional[date] = None
    ) -> Tuple[List[Document], List[Decision]]:
        """Returns (allowed_docs, decisions). `decisions` covers every
        candidate that was checked; `allowed_docs` contains ONLY the
        documents whose decision was ALLOW -- this is the sole gate through
        which content may reach the rest of the pipeline."""
        decisions = [self.check_access(user, doc, today) for doc in documents]
        allowed_ids = {d.document_id for d in decisions if d.allowed}
        allowed_docs = [doc for doc in documents if doc.document_id in allowed_ids]
        return allowed_docs, decisions
