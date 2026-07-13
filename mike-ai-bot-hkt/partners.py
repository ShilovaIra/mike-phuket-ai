from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from uuid import UUID

INTRO = "Вот партнёры для обмена рублей:"
FALLBACK = (
    "Пока нет доступных партнёров по обмену. "
    "Напишите Майку — подскажу, что можно сделать."
)
CAPTION_CTA = "⬇️ Обменять сейчас ⬇️"
MONEY_EXCHANGE_TYPE = "money_exchange"

# Bot package root (directory containing partners.py / media/).
PACKAGE_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Partner:
    id: UUID
    name: str
    type: str
    referral_url: str
    blurb: str | None
    sort_order: int
    logo_path: str | None = None


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


def build_partner_caption_html(partner: Partner) -> str:
    name_link = (
        f'💰 <a href="{escape(partner.referral_url, quote=True)}">'
        f"{escape(partner.name)}</a> 💰"
    )
    parts = [name_link]
    if partner.blurb:
        parts.append(f"✅ {escape(partner.blurb)}")
    parts.append(CAPTION_CTA)
    return "\n\n".join(parts)


def build_partner_button_text(partner: Partner) -> str:
    return f"Обменять с {partner.name}"


def build_partner_cards(
    partners: Sequence[Partner],
) -> tuple[str, list[PartnerCard]]:
    if not partners:
        return FALLBACK, []

    cards = [
        PartnerCard(
            caption_html=build_partner_caption_html(partner),
            button_text=build_partner_button_text(partner),
            referral_url=partner.referral_url,
            logo_path=partner.logo_path,
        )
        for partner in partners
    ]
    return INTRO, cards
