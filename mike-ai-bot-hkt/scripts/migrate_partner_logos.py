"""Move bundled partner logos (media/partners/…) into S3 storage.

Also sets the bucket rule that deletes abandoned admin uploads under tmp/ after
one day. Safe to re-run: partners whose logo is already in storage are skipped.

Run on each Droplet after the deploy that ships this script (staging first):

    docker compose exec bot python scripts/migrate_partner_logos.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from db.store import SessionStore  # noqa: E402
from db.url import resolve_database_url  # noqa: E402
from partner_logo_migration import migrate_bundled_logos  # noqa: E402
from storage import AssetStorage, StorageError  # noqa: E402


async def main() -> int:
    storage = AssetStorage.from_env(os.environ)
    if storage is None:
        print("!! S3_* settings incomplete in .env")
        return 1
    database_url = resolve_database_url()
    if not database_url:
        print("!! DATABASE_URL or POSTGRES_* is required")
        return 1

    try:
        storage.expire_prefix("tmp/", days=1)
        print("ok      tmp/ uploads expire after 1 day")
    except StorageError as exc:
        # Limited Access Spaces keys can upload objects but cannot set bucket
        # lifecycle rules. Abandoned tmp/ files are cheap; skip and migrate.
        print(f"!! skipped tmp/ expiry rule ({exc})")

    store = await SessionStore.create(database_url)
    try:
        report = await migrate_bundled_logos(store, storage)
    finally:
        await store.close()

    for item in report.migrated:
        print(f"moved   {item.source} -> {item.key}")
    for item in report.missing:
        print(f"!! missing file {item.source} (partner {item.partner_id}), left as is")
    if not report.migrated and not report.missing:
        print("ok      nothing to migrate")
    return 1 if report.missing else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
