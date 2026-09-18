"""SentinelRAG API -- FastAPI backend wrapping the existing pipeline.

Run with:
    uvicorn api:app --reload --port 8000

Everything security-critical (sentinel.authorization, sentinel.conflict_resolver)
is untouched by this file. This layer only adds: identity (login -> JWT),
and an admin ingestion endpoint. The pipeline itself is called exactly as
the CLI calls it, just with a DB-backed document store instead of a JSON file.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from sentinel.audit import AuditLog
from sentinel.auth import create_access_token, decode_access_token, verify_password
from sentinel.document_repository import DocumentRepository
from sentinel.ingestion import extract_text
from sentinel.models import User
from sentinel.orchestrator import SentinelRAGPipeline
from sentinel.user_repository import UserRepository

load_dotenv()

DB_PATH = os.getenv("SENTINELRAG_DB", "sentinelrag.db")

app = FastAPI(title="SentinelRAG API")

# The React dev server runs on a different origin (port) than this API.
# Restricted to localhost dev ports -- not a wildcard -- since this still
# carries real bearer tokens.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users = UserRepository(DB_PATH)
documents = DocumentRepository(DB_PATH)
audit = AuditLog(DB_PATH)
pipeline = SentinelRAGPipeline(documents, audit_log=audit)

security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    question: str


def get_current_claims(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        return decode_access_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_admin(claims: dict = Depends(get_current_claims)) -> dict:
    if not claims.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return claims


@app.post("/auth/login")
def login(body: LoginRequest):
    record = users.get_by_username(body.username)
    if not record or not verify_password(body.password, record.password_hash):
        # Same error for "no such user" and "wrong password" -- do not
        # reveal which one it was.
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(record)
    return {
        "access_token": token,
        "user": {
            "user_id": record.user_id,
            "username": record.username,
            "role": record.role,
            "department": record.department,
            "clearance": record.clearance,
            "is_admin": record.is_admin,
        },
    }


@app.get("/auth/me")
def me(claims: dict = Depends(get_current_claims)):
    return claims


@app.post("/query")
def query(body: QueryRequest, claims: dict = Depends(get_current_claims)):
    # The user's role/department/clearance come ONLY from the verified JWT
    # claims (set by the server at login), never from the request body.
    user = User(claims["sub"], claims["role"], claims["department"], claims["clearance"])
    return pipeline.run(user, body.question)


@app.post("/documents")
async def upload_document(
    title: str = Form(...),
    classification: str = Form(...),
    effective_date: str = Form(...),
    allowed_departments: Optional[str] = Form(None),
    allowed_roles: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    claims: dict = Depends(require_admin),
):
    if file is not None:
        raw = await file.read()
        content = extract_text(file.filename, raw)
    elif text_content:
        content = text_content
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or text_content")

    # An empty/omitted allowed_departments or allowed_roles means "no
    # restriction on this axis" -- not "denied to everyone". This is
    # consistent with AuthorizationGatekeeper.check_access, which only
    # enforces a department/role check when the corresponding list is
    # non-empty.
    doc = documents.add_document(
        title=title,
        classification=classification,
        content=content,
        allowed_departments=[d.strip() for d in (allowed_departments or "").split(",") if d.strip()],
        allowed_roles=[r.strip() for r in (allowed_roles or "").split(",") if r.strip()],
        effective_date=effective_date,
        version=version,
        uploaded_by=claims["sub"],
    )
    return {"document_id": doc.document_id, "title": doc.title, "version": doc.version}


@app.get("/documents")
def list_documents(claims: dict = Depends(require_admin)):
    return documents.list_metadata()
