from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from .models import Document

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    classification TEXT NOT NULL,
    content TEXT NOT NULL,
    version TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    allowed_departments TEXT NOT NULL,
    allowed_roles TEXT NOT NULL,
    allowed_users TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active',
    owner TEXT,
    department TEXT,
    uploaded_by TEXT,
    uploaded_at TEXT NOT NULL
);
"""

_COLUMNS = [
    "document_id", "title", "classification", "content", "version", "effective_date",
    "allowed_departments", "allowed_roles", "allowed_users", "status", "owner",
    "department", "uploaded_by", "uploaded_at",
]


class DocumentRepository:
    """SQLite-backed document store.

    Exposes the same `.all()` contract as the JSON-based DocumentStore used
    by the CLI, so SentinelRAGPipeline, RetrievalAgent, and everything
    downstream can use either interchangeably without any change -- this
    repository is a drop-in replacement, not a parallel code path.
    """

    def __init__(self, db_path: str = "sentinelrag.db") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._lock = threading.Lock()

    def all(self) -> List[Document]:
        rows = self._conn.execute(f"SELECT {', '.join(_COLUMNS)} FROM documents").fetchall()
        return [self._row_to_document(dict(zip(_COLUMNS, row))) for row in rows]

    def _row_to_document(self, row: dict) -> Document:
        return Document(
            document_id=row["document_id"],
            title=row["title"],
            classification=row["classification"],
            content=row["content"],
            version=row["version"],
            effective_date=row["effective_date"],
            allowed_departments=json.loads(row["allowed_departments"]),
            allowed_roles=json.loads(row["allowed_roles"]),
            allowed_users=json.loads(row["allowed_users"]),
            status=row["status"],
            owner=row["owner"],
            department=row["department"],
        )

    def next_version(self, title: str) -> str:
        """Auto-increments the major version number for a given title, e.g.
        '1.0' -> '2.0'. Used when an admin uploads a new version without
        specifying one explicitly."""
        rows = self._conn.execute("SELECT version FROM documents WHERE title = ?", (title,)).fetchall()
        if not rows:
            return "1.0"
        max_major = 0
        for (v,) in rows:
            try:
                major = int(float(v))
            except ValueError:
                major = 0
            max_major = max(max_major, major)
        return f"{max_major + 1}.0"

    def add_document(
        self,
        title: str,
        classification: str,
        content: str,
        allowed_departments: List[str],
        allowed_roles: List[str],
        effective_date: str,
        uploaded_by: str,
        version: Optional[str] = None,
        allowed_users: Optional[List[str]] = None,
        owner: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Document:
        document_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
        version = version or self.next_version(title)
        row = dict(
            document_id=document_id,
            title=title,
            classification=classification,
            content=content,
            version=version,
            effective_date=effective_date,
            allowed_departments=json.dumps(allowed_departments),
            allowed_roles=json.dumps(allowed_roles),
            allowed_users=json.dumps(allowed_users or []),
            status="active",
            owner=owner,
            department=department,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            placeholders = ", ".join("?" for _ in _COLUMNS)
            self._conn.execute(
                f"INSERT INTO documents ({', '.join(_COLUMNS)}) VALUES ({placeholders})",
                [row[c] for c in _COLUMNS],
            )
            self._conn.commit()
        return self._row_to_document(row)

    def revoke(self, document_id: str) -> None:
        with self._lock:
            self._conn.execute("UPDATE documents SET status = 'revoked' WHERE document_id = ?", (document_id,))
            self._conn.commit()

    def list_metadata(self) -> List[dict]:
        cols = ["document_id", "title", "classification", "version", "effective_date", "status", "uploaded_by", "uploaded_at"]
        rows = self._conn.execute(
            f"SELECT {', '.join(cols)} FROM documents ORDER BY title, version"
        ).fetchall()
        return [dict(zip(cols, row)) for row in rows]
