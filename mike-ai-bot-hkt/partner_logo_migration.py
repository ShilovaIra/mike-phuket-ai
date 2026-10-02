"""One-off move of bundled partner logos (media/…) into dynamic-asset storage."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from db.store import SessionStore
from partners import PACKAGE_ROOT, is_bundled_logo
from storage import AssetStorage

_CONTENT_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


@dataclass(frozen=True)
class MigratedLogo:
    partner_id: UUID
    source: str
    key: str


@dataclass(frozen=True)
class MissingLogo:
    partner_id: UUID
    source: str


@dataclass
class MigrationReport:
    migrated: list[MigratedLogo] = field(default_factory=list)
    missing: list[MissingLogo] = field(default_factory=list)


async def migrate_bundled_logos(
    store: SessionStore, storage: AssetStorage, *, root: Path = PACKAGE_ROOT
) -> MigrationReport:
    report = MigrationReport()
    for partner in await store.list_partners():
        source = partner.logo_path or ""
        if not is_bundled_logo(source):
            continue
        path = root / source
        if not path.is_file():
            report.missing.append(MissingLogo(partner_id=partner.id, source=source))
            continue
        data = path.read_bytes()
        suffix = path.suffix.lower()
        digest = hashlib.sha256(data).hexdigest()[:12]
        key = f"partners/{partner.id}/logo-{digest}{suffix}"
        storage.upload(key, data, _CONTENT_TYPES[suffix])
        await store.set_partner_logo(partner.id, key)
        report.migrated.append(MigratedLogo(partner_id=partner.id, source=source, key=key))
    return report
