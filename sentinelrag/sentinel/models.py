from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# Ordered so that CLEARANCE_LEVELS[a] > CLEARANCE_LEVELS[b] means "a requires
# more access than b". Used to compare a document's classification against a
# user's clearance -- the single most important comparison in this system.
CLEARANCE_LEVELS = {
    "Public": 0,
    "Internal": 1,
    "Confidential": 2,
    "Restricted": 3,
}


@dataclass
class User:
    user_id: str
    role: str
    department: str
    clearance: str

    @staticmethod
    def from_dict(d: dict) -> "User":
        return User(
            user_id=d["user_id"],
            role=d["role"],
            department=d["department"],
            clearance=d["clearance"],
        )


@dataclass
class Document:
    document_id: str
    title: str
    classification: str
    content: str
    version: str = "1.0"
    effective_date: str = "1970-01-01"
    allowed_departments: list = field(default_factory=list)
    allowed_roles: list = field(default_factory=list)
    allowed_users: list = field(default_factory=list)
    status: str = "active"
    owner: Optional[str] = None
    department: Optional[str] = None

    @staticmethod
    def from_dict(d: dict) -> "Document":
        return Document(
            document_id=d["document_id"],
            title=d["title"],
            classification=d["classification"],
            content=d["content"],
            version=d.get("version", "1.0"),
            effective_date=d.get("effective_date", "1970-01-01"),
            allowed_departments=d.get("allowed_departments", []),
            allowed_roles=d.get("allowed_roles", []),
            allowed_users=d.get("allowed_users", []),
            status=d.get("status", "active"),
            owner=d.get("owner"),
            department=d.get("department"),
        )

    @property
    def effective_date_obj(self) -> date:
        return date.fromisoformat(self.effective_date)
