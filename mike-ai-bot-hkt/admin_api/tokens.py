from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

DEFAULT_TTL_HOURS = 12


def jwt_secret() -> str:
    secret = os.environ.get("ADMIN_JWT_SECRET")
    if not secret:
        raise RuntimeError("ADMIN_JWT_SECRET is not set")
    return secret


def create_access_token(*, admin_id: UUID, email: str, ttl_hours: int = DEFAULT_TTL_HOURS) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(admin_id),
        "email": email,
        "role": "operator",
        "iat": now,
        "exp": now + timedelta(hours=ttl_hours),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, jwt_secret(), algorithms=["HS256"], leeway=60)


LOGO_UPLOAD_TTL_HOURS = 1
_LOGO_UPLOAD_PURPOSE = "logo_upload"


def create_logo_upload_token(*, key: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "purpose": _LOGO_UPLOAD_PURPOSE,
        "key": key,
        "iat": now,
        "exp": now + timedelta(hours=LOGO_UPLOAD_TTL_HOURS),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def decode_logo_upload_token(token: str) -> str:
    """Return the staged tmp/ key, or raise jwt.PyJWTError."""
    payload = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
    key = payload.get("key")
    if payload.get("purpose") != _LOGO_UPLOAD_PURPOSE or not isinstance(key, str):
        raise jwt.InvalidTokenError("not a logo upload token")
    if not key.startswith("tmp/"):
        raise jwt.InvalidTokenError("not a staged upload")
    return key
