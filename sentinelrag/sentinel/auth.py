from __future__ import annotations

import os
import time

import bcrypt
import jwt

from .user_repository import UserRecord

# In a real deployment this MUST come from a secret manager / env var, never
# a hardcoded default. The fallback here is clearly a dev-only value so
# nobody mistakes it for production-safe.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-before-any-real-deployment")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 3600


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(record: UserRecord) -> str:
    """Encodes role/department/clearance as SIGNED claims, taken from the
    server's own user record at login time -- never from anything a client
    sends. The client carries the token, but cannot forge or edit its
    contents without the server's secret, which is what makes it safe for
    downstream authorization checks to trust these claims."""
    payload = {
        "sub": record.user_id,
        "username": record.username,
        "role": record.role,
        "department": record.department,
        "clearance": record.clearance,
        "is_admin": record.is_admin,
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
