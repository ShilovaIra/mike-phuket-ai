from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from uuid import UUID

# Bot package root (directory containing partners.py / media/).
PACKAGE_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PartnerType:
    slug: str
    is_menu_visible: bool
    sort_order: int
    button_label: str
    topic_label: str
    intro: str
    fallback: str
    caption_emoji: str
    caption_cta: str
    button_template: str
    follow_up_text: str = ""


@dataclass(frozen=True)
class Partner:
    id: UUID
    name: str
    type: str
    referral_url: str
    blurb: str | None
    sort_order: int
    logo_path: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class PartnerCard:
    caption_html: str
    button_text: str
    referral_url: str
    logo_path: str | None


def resolve_logo_path(logo_path: str | None, *, root: Path = PACKAGE_ROOT) -> Path | None:
    if not logo_path:
        return None
    path = Path(logo_path)
    if not path.is_absolute():
        path = root / path
    if path.is_file():
        return path
    return None


def build_partner_caption_html(partner: Partner, partner_type: PartnerType) -> str:
    emoji = partner_type.caption_emoji
    name_link = (
        f'{emoji} <a href="{escape(partner.referral_url, quote=True)}">'
        f"{escape(partner.name)}</a> {emoji}"
    )
    parts = [name_link]
    if partner.blurb:
        parts.append(f"✅ {escape(partner.blurb)}")
    parts.append(partner_type.caption_cta)
    return "\n\n".join(parts)


def build_partner_button_text(partner: Partner, partner_type: PartnerType) -> str:
    return partner_type.button_template.format(name=partner.name)


def build_partner_cards(
    partners: Sequence[Partner],
    partner_type: PartnerType,
) -> tuple[str, list[PartnerCard]]:
    if not partners:
        return partner_type.fallback, []

    cards = [
        PartnerCard(
            caption_html=build_partner_caption_html(partner, partner_type),
            button_text=build_partner_button_text(partner, partner_type),
            referral_url=partner.referral_url,
            logo_path=partner.logo_path,
        )
        for partner in partners
    ]
    return partner_type.intro, cards
