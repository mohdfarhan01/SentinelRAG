from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS queries (
    query_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS authorization_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    allowed INTEGER NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_used (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    version TEXT
);

CREATE TABLE IF NOT EXISTS answers (
    query_id TEXT PRIMARY KEY,
    answer TEXT NOT NULL,
    retrieved_count INTEGER NOT NULL,
    authorized_count INTEGER NOT NULL,
    blocked_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id TEXT NOT NULL,
    call_index INTEGER NOT NULL,
    search_query TEXT NOT NULL,
    retrieved_count INTEGER NOT NULL,
    authorized_count INTEGER NOT NULL,
    blocked_count INTEGER NOT NULL
);
"""


class AuditLog:
    """Deterministic, automatic logging -- never exposed as an LLM tool.

    A tool the agent must remember to call is a tool it can forget to
    call. Every stage of the pipeline writes here directly as a side
    effect of running, independent of what the LLM does or claims to have
    done, which is what makes the audit trail trustworthy.
    """

    def __init__(self, db_path: str = "audit_log.db") -> None:
        self.db_path = db_path
        # check_same_thread=False: a web API serves requests from a thread
        # pool, unlike the single-threaded CLI this class was first written
        # for. The lock below is what actually keeps writes safe across
        # those threads.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._lock = threading.Lock()

    def log_query(self, query_id: str, user_id: str, question: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO queries (query_id, user_id, question, created_at) VALUES (?, ?, ?, ?)",
                (query_id, user_id, question, datetime.now(timezone.utc).isoformat()),
            )
            self._conn.commit()

    def log_decisions(self, query_id: str, decisions: Iterable) -> None:
        with self._lock:
            self._conn.executemany(
                "INSERT INTO authorization_decisions (query_id, document_id, allowed, reason) VALUES (?, ?, ?, ?)",
                [(query_id, d.document_id, int(d.allowed), d.reason) for d in decisions],
            )
            self._conn.commit()

    def log_evidence(self, query_id: str, documents: Iterable) -> None:
        with self._lock:
            self._conn.executemany(
                "INSERT INTO evidence_used (query_id, document_id, version) VALUES (?, ?, ?)",
                [(query_id, d.document_id, d.version) for d in documents],
            )
            self._conn.commit()

    def log_tool_calls(self, query_id: str, tool_calls: Iterable) -> None:
        """Records each search the agentic loop actually performed --
        this is the trace that answers "what did the agent decide on its
        own": how many times it searched and how it reformulated the
        query between calls."""
        with self._lock:
            self._conn.executemany(
                "INSERT INTO agent_tool_calls "
                "(query_id, call_index, search_query, retrieved_count, authorized_count, blocked_count) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (query_id, i, c["query"], c["retrieved"], c["authorized"], c["blocked"])
                    for i, c in enumerate(tool_calls)
                ],
            )
            self._conn.commit()

    def log_answer(self, query_id: str, answer: str, retrieved: int, authorized: int, blocked: int) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO answers (query_id, answer, retrieved_count, authorized_count, blocked_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (query_id, answer, retrieved, authorized, blocked),
            )
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()
