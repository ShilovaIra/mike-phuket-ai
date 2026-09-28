from __future__ import annotations

from dataclasses import asdict

from partners import Partner, is_bundled_logo
from storage import AssetStorage


def partner_payload(partner: Partner, storage: AssetStorage | None) -> dict:
    payload = asdict(partner)
    payload["id"] = str(partner.id)
    payload["logo_path"] = partner.logo_path or ""
    payload["logo_url"] = (
        storage.public_url(partner.logo_path)
        if storage is not None and partner.logo_path and not is_bundled_logo(partner.logo_path)
        else ""
    )
    payload["blurb"] = partner.blurb or ""
    return payload
