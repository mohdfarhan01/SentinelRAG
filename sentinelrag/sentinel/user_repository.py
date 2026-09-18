from __future__ import annotations

import sqlite3
import threading
import uuid
from dataclasses import dataclass
from typing import Optional

from .models import User

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    clearance TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
);
"""


@dataclass
class UserRecord:
    user_id: str
    username: str
    password_hash: str
    role: str
    department: str
    clearance: str
    is_admin: bool

    def to_user(self) -> User:
        return User(self.user_id, self.role, self.department, self.clearance)


class UserRepository:
    """The authoritative identity directory. This is the ONLY place a
    user's role/department/clearance may come from once real login is in
    the picture -- never from anything the client sends in a request.
    """

    def __init__(self, db_path: str = "sentinelrag.db") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        self._lock = threading.Lock()

    def get_by_username(self, username: str) -> Optional[UserRecord]:
        row = self._conn.execute(
            "SELECT user_id, username, password_hash, role, department, clearance, is_admin "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        return UserRecord(row[0], row[1], row[2], row[3], row[4], row[5], bool(row[6]))

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: str,
        department: str,
        clearance: str,
        is_admin: bool = False,
        user_id: Optional[str] = None,
    ) -> UserRecord:
        user_id = user_id or f"U{uuid.uuid4().hex[:6].upper()}"
        with self._lock:
            self._conn.execute(
                "INSERT INTO users (user_id, username, password_hash, role, department, clearance, is_admin) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, password_hash, role, department, clearance, int(is_admin)),
            )
            self._conn.commit()
        return UserRecord(user_id, username, password_hash, role, department, clearance, is_admin)
