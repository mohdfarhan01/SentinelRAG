"""Tests for POST /auth/signup.

The critical property under test: a client cannot escalate its own
privileges through signup, no matter what it sends. Every other signup
behavior (duplicate rejection, password length) is ordinary validation,
but the privilege-escalation test is the one that actually protects the
project's security premise.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Each test gets its own throwaway SQLite file so signups in one test
    # can't collide with another, and nothing here touches the real
    # sentinelrag.db used by manual runs.
    db_path = tmp_path / "test_signup.db"
    monkeypatch.setenv("SENTINELRAG_DB", str(db_path))

    import api as api_module
    import importlib

    importlib.reload(api_module)
    return TestClient(api_module.app)


def unique_username() -> str:
    return f"newuser_{uuid.uuid4().hex[:8]}"


def test_signup_creates_a_public_non_admin_account(client):
    username = unique_username()
    res = client.post("/auth/signup", json={"username": username, "password": "correcthorse"})

    assert res.status_code == 200
    body = res.json()
    assert body["user"]["username"] == username
    assert body["user"]["clearance"] == "Public"
    assert body["user"]["department"] == "General"
    assert body["user"]["role"] == "Employee"
    assert body["user"]["is_admin"] is False
    assert body["access_token"]


def test_signup_cannot_escalate_privileges_via_extra_fields(client):
    """The one test that actually matters: even if a client sends
    clearance/role/is_admin in the signup body, the account created must
    still be Public/Employee/General/non-admin. If this ever fails, the
    signup endpoint has become a privilege-escalation vulnerability."""
    username = unique_username()
    res = client.post(
        "/auth/signup",
        json={
            "username": username,
            "password": "correcthorse",
            "clearance": "Restricted",
            "role": "Executive",
            "department": "Executive",
            "is_admin": True,
        },
    )

    assert res.status_code == 200
    user = res.json()["user"]
    assert user["clearance"] == "Public"
    assert user["role"] == "Employee"
    assert user["department"] == "General"
    assert user["is_admin"] is False


def test_signup_rejects_duplicate_username(client):
    username = unique_username()
    first = client.post("/auth/signup", json={"username": username, "password": "correcthorse"})
    assert first.status_code == 200

    second = client.post("/auth/signup", json={"username": username, "password": "anotherpassword"})
    assert second.status_code == 409


def test_signup_rejects_short_password(client):
    res = client.post(
        "/auth/signup", json={"username": unique_username(), "password": "short"}
    )
    assert res.status_code == 400


def test_signed_up_user_can_immediately_log_in(client):
    username = unique_username()
    signup_res = client.post(
        "/auth/signup", json={"username": username, "password": "correcthorse"}
    )
    assert signup_res.status_code == 200

    login_res = client.post(
        "/auth/login", json={"username": username, "password": "correcthorse"}
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["username"] == username
