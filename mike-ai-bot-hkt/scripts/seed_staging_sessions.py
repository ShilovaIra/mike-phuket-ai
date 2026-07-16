#!/usr/bin/env python3
"""One-time staging seed: import half of a RAM export into Postgres.

Intended to run once when establishing staging. Refuses if users already exist.

  # Write a half-sized JSON first (local, do not commit):
  python scripts/seed_staging_sessions.py \\
    ../mike_sessions_export.json \\
    --write-subset ../mike_sessions_export_staging.json

  # On the Droplet (after docker compose is up):
  docker compose run --rm bot python scripts/seed_staging_sessions.py \\
    --fraction 1 mike_sessions_export_staging.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db.import_sessions import import_from_export, write_export_subset


async def _user_count(store) -> int:
    async with store._pool.acquire() as conn:  # noqa: SLF001 — seed-only probe
        return int(await conn.fetchval("SELECT count(*) FROM users") or 0)


async def seed(export_path: Path, *, fraction: float, force: bool) -> dict[str, int]:
    from dotenv import load_dotenv

    from db.store import SessionStore
    from db.url import resolve_database_url

    load_dotenv()
    database_url = resolve_database_url()
    if not database_url:
        raise SystemExit("DATABASE_URL or POSTGRES_USER/PASSWORD/DB is required")

    store = await SessionStore.create(database_url)
    try:
        existing = await _user_count(store)
        if existing and not force:
            raise SystemExit(
                f"Refusing to seed: database already has {existing} user(s). "
                "This script is one-shot for a fresh staging DB. "
                "Pass --force only if you intentionally want to add more."
            )
        return await import_from_export(store, export_path, fraction=fraction)
    finally:
        await store.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-time staging seed from mike_sessions_export.json (default: half)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="../mike_sessions_export.json",
        help="Full export JSON (source for subset or import)",
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.5,
        help="Fraction of sessions to keep/import (default: 0.5)",
    )
    parser.add_argument(
        "--write-subset",
        metavar="DEST",
        help="Only write a subset JSON to DEST (no DB import). Do not commit the file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow seed even if users table is non-empty",
    )
    args = parser.parse_args()

    export_path = Path(args.path).resolve()
    if not export_path.exists():
        raise SystemExit(f"Export file not found: {export_path}")

    if args.write_subset:
        dest = Path(args.write_subset).resolve()
        meta = write_export_subset(export_path, dest, fraction=args.fraction)
        print("Wrote staging subset (do not commit):")
        for key, value in meta.items():
            print(f"  {key}: {value}")
        return

    stats = asyncio.run(seed(export_path, fraction=args.fraction, force=args.force))
    print("Staging seed complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
