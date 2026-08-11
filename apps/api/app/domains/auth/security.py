import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from typing import Any

from fastapi import HTTPException, status

PBKDF2_ITERATIONS = 600_000
TOKEN_TTL_SECONDS = 3600
REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 3600


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _secret() -> bytes:
    value = os.getenv("JWT_SECRET")
    if not value:
        raise RuntimeError("JWT_SECRET must be configured")
    return value.encode()


def create_access_token(
    user_id: uuid.UUID, role: str, ttl: int = TOKEN_TTL_SECONDS, credential_version: int = 1
) -> str:
    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(
        json.dumps(
            {
                "sub": str(user_id),
                "role": role,
                "cv": credential_version,
                "iat": now,
                "exp": now + ttl,
            },
            separators=(",", ":"),
        ).encode()
    )
    message = f"{header}.{payload}"
    signature = _b64(hmac.new(_secret(), message.encode(), hashlib.sha256).digest())
    return f"{message}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        header, payload, signature = token.split(".")
        message = f"{header}.{payload}"
        expected = _b64(hmac.new(_secret(), message.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise error
        claims = json.loads(_unb64(payload))
        if int(claims["exp"]) <= int(time.time()) or not claims.get("sub"):
            raise error
        return claims
    except HTTPException:
        raise
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise error from exc
