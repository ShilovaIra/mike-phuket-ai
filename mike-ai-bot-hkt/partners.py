from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

INTRO = "Вот партнёры для обмена рублей:"
FALLBACK = (
    "Пока нет доступных партнёров по обмену. "
    "Напишите Майку — подскажу, что можно сделать."
)
MONEY_EXCHANGE_TYPE = "money_exchange"


@dataclass(frozen=True)
class Partner:
    id: UUID
    name: str
    type: str
    referral_url: str
    blurb: str | None
    sort_order: int


def build_partner_list_replies(partners: Sequence[Partner]) -> list[str]:
    if not partners:
        return [FALLBACK]

    messages = [INTRO]
    for partner in partners:
        parts = [partner.name]
        if partner.blurb:
            parts.append(partner.blurb)
        parts.append(partner.referral_url)
        messages.append("\n\n".join(parts))
    return messages
