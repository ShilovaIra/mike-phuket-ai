"""Build a safe PostgreSQL URL from env (handles special chars in passwords)."""

from __future__ import annotations

import os
from urllib.parse import quote_plus, urlparse


def resolve_database_url() -> str | None:
    """Prefer POSTGRES_* parts when present; URL-encode user/password.

    Docker Compose should set POSTGRES_HOST=db instead of injecting an
    unencoded DATABASE_URL (passwords with @:#/% break asyncpg DSNs).
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    raw = os.getenv("DATABASE_URL")

    if user and password and db_name:
        if not host and raw:
            parsed = urlparse(raw)
            host = parsed.hostname or None
            if parsed.port:
                port = str(parsed.port)
        host = host or "localhost"
        return (
            f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
            f"@{host}:{port}/{db_name}"
        )

    return raw
