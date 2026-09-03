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
