import pytest

from sentinel.auth import create_access_token, decode_access_token, hash_password, verify_password
from sentinel.user_repository import UserRecord


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_password_hash_is_not_plaintext():
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_token_roundtrip_carries_server_assigned_claims():
    record = UserRecord(
        user_id="U205",
        username="u205",
        password_hash="unused",
        role="Marketing",
        department="Marketing",
        clearance="Internal",
        is_admin=False,
    )
    token = create_access_token(record)
    claims = decode_access_token(token)

    assert claims["sub"] == "U205"
    assert claims["role"] == "Marketing"
    assert claims["department"] == "Marketing"
    assert claims["clearance"] == "Internal"
    assert claims["is_admin"] is False


def test_tampered_token_is_rejected():
    record = UserRecord("U102", "u102", "unused", "Finance", "Finance", "Internal", False)
    token = create_access_token(record)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(Exception):
        decode_access_token(tampered)
