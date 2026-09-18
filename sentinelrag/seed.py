"""Seeds sentinelrag.db with demo login accounts and the official PS14 test
documents, so the GUI starts pre-populated with known-good scenarios.

Run once:
    python seed.py

Safe to re-run: skips seeding whatever already exists.
"""

from __future__ import annotations

import os

from sentinel.auth import hash_password
from sentinel.document_repository import DocumentRepository
from sentinel.user_repository import UserRepository

DB_PATH = os.getenv("SENTINELRAG_DB", "sentinelrag.db")

DEMO_PASSWORD = "password123"  # hackathon demo only -- never do this in production


def seed_users(users: UserRepository) -> None:
    demo_users = [
        ("u102", "Finance", "Finance", "Internal", False, "U102"),
        ("u205", "Marketing", "Marketing", "Internal", False, "U205"),
        ("u301", "Finance", "Finance", "Internal", False, "U301"),
        ("admin", "IT", "IT", "Restricted", True, "UADMIN"),
    ]
    for username, role, department, clearance, is_admin, user_id in demo_users:
        if users.get_by_username(username):
            print(f"  user '{username}' already exists, skipping")
            continue
        users.create_user(
            username=username,
            password_hash=hash_password(DEMO_PASSWORD),
            role=role,
            department=department,
            clearance=clearance,
            is_admin=is_admin,
            user_id=user_id,
        )
        print(f"  created '{username}' (role={role}, dept={department}, clearance={clearance}, admin={is_admin})")


def seed_documents(documents: DocumentRepository) -> None:
    if documents.list_metadata():
        print("  documents already seeded, skipping")
        return

    fixtures = [
        dict(
            title="Q4 Revenue Forecast", classification="Internal",
            content="Q4 projected revenue is 120 crore.",
            allowed_departments=["Finance"], allowed_roles=["Finance"],
            effective_date="2026-09-01", version="2.0",
        ),
        dict(
            title="Engineering Roadmap", classification="Internal",
            content="The next platform release is planned for October.",
            allowed_departments=["Engineering"], allowed_roles=["Engineer"],
            effective_date="2026-08-01", version="1.0",
        ),
        dict(
            title="Q4 Revenue Forecast", classification="Restricted",
            content="Q4 projected revenue is 145 crore.",
            allowed_departments=["Executive"], allowed_roles=["Executive"],
            effective_date="2026-09-01", version="3.0",
        ),
        dict(
            title="Q4 Forecast", classification="Internal",
            content="Q4 projected revenue is 110 crore.",
            allowed_departments=["Finance"], allowed_roles=["Finance"],
            effective_date="2026-06-01", version="1.0",
        ),
        dict(
            title="Q4 Forecast", classification="Internal",
            content="Q4 projected revenue is 125 crore.",
            allowed_departments=["Finance"], allowed_roles=["Finance"],
            effective_date="2026-09-01", version="2.0",
        ),
    ]
    for fx in fixtures:
        documents.add_document(uploaded_by="seed", **fx)
    print(f"  seeded {len(fixtures)} documents")


if __name__ == "__main__":
    print("Seeding users...")
    seed_users(UserRepository(DB_PATH))
    print("Seeding documents...")
    seed_documents(DocumentRepository(DB_PATH))
    print(f"\nDone. Demo login password for all seeded accounts: {DEMO_PASSWORD}")
