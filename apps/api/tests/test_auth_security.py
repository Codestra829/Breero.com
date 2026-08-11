import uuid

import pytest
from fastapi import HTTPException

from app.domains.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    encoded = hash_password("a long secure password")
    assert encoded != "a long secure password"
    assert verify_password("a long secure password", encoded)
    assert not verify_password("wrong password", encoded)


def test_access_token_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-not-for-production")
    user_id = uuid.uuid4()
    claims = decode_access_token(create_access_token(user_id, "operations"))
    assert claims["sub"] == str(user_id)
    assert claims["role"] == "operations"


def test_tampered_access_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "test-secret-that-is-not-for-production")
    token = create_access_token(uuid.uuid4(), "customer")
    with pytest.raises(HTTPException) as error:
        decode_access_token(token[:-1] + ("a" if token[-1] != "a" else "b"))
    assert error.value.status_code == 401
