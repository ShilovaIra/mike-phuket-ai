from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class KnowledgeBaseEntry:
    id: UUID
    name: str
    partner_id: UUID | None
    place_id: UUID | None
    referral_url: str
    maps_url: str
    blurb: str
    kind: str
    is_visible: bool


def format_for_prompt(entries: list[KnowledgeBaseEntry]) -> str:
    entries = [entry for entry in entries if entry.is_visible]
    if not entries:
        return ""
    lines = [
        "База знаний — предлагай эти места и партнёров в первую очередь.",
        "Если вопрос подходит к строкам ниже, предложи все подходящие "
        "и укажи их ссылки символ в символ. Не ищи в Google и не добавляй другие места.",
        "Если ни одна строка не подходит, ищи в Google как обычно.",
    ]
    for entry in entries:
        label = entry.name if not entry.kind else f"{entry.name} ({entry.kind})"
        parts = [label]
        if entry.blurb:
            parts.append(entry.blurb)
        if entry.referral_url:
            parts.append(entry.referral_url)
        if entry.maps_url:
            parts.append(entry.maps_url)
        lines.append("- " + " ".join(parts))
    return "\n".join(lines)
