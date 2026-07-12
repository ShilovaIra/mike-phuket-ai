"""One-time import of RAM export JSON into PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db.import_sessions import import_from_export
from db.store import SessionStore


async def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Import mike_sessions_export.json into Postgres")
    parser.add_argument(
        "path",
        nargs="?",
        default="../mike_sessions_export.json",
        help="Path to export JSON",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=1.0,
        help="Import only this fraction of sessions (sorted by user id)",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    export_path = Path(args.path).resolve()
    if not export_path.exists():
        raise SystemExit(f"Export file not found: {export_path}")

    store = await SessionStore.create(database_url)
    try:
        stats = await import_from_export(store, export_path, fraction=args.fraction)
    finally:
        await store.close()

    print("Import complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
