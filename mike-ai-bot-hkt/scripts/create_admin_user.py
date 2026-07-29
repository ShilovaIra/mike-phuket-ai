from __future__ import annotations

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

from db.store import SessionStore


async def _main(email: str, password: str) -> None:
    load_dotenv()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    store = await SessionStore.create(database_url)
    try:
        admin = await store.create_admin_user(email=email, password=password)
        print(f"Created admin {admin.email} ({admin.id})")
    finally:
        await store.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create an admin panel user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args(argv)
    asyncio.run(_main(args.email, args.password))


if __name__ == "__main__":
    main(sys.argv[1:])
