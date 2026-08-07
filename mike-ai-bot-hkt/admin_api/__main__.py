from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv

from db.url import resolve_database_url


def main() -> None:
    load_dotenv()
    if not resolve_database_url():
        raise RuntimeError("DATABASE_URL or POSTGRES_* is required")
    if not os.environ.get("ADMIN_JWT_SECRET"):
        raise RuntimeError("ADMIN_JWT_SECRET is required")

    host = os.environ.get("ADMIN_API_HOST", "0.0.0.0")
    port = int(os.environ.get("ADMIN_API_PORT", "8000"))
    uvicorn.run("admin_api.app:create_app", factory=True, host=host, port=port)


if __name__ == "__main__":
    main()
