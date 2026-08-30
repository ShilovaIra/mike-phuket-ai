from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from admin_api.tokens import jwt_secret

DEFAULT_TTL_HOURS = 12


def create_partner_access_token(
    *, partner_user_id: UUID, email: str, ttl_hours: int = DEFAULT_TTL_HOURS
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(partner_user_id),
        "email": email,
        "role": "partner_user",
        "iat": now,
        "exp": now + timedelta(hours=ttl_hours),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")
