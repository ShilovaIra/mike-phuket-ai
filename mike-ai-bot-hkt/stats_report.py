"""Format bot analytics for the admin /stats command."""

from __future__ import annotations

from collections.abc import Sequence

from db.store import BotStats, TopicCount
from partners import PartnerType
from topics import TOPIC_ORDER, TOPIC_REAL_ESTATE
from topic_labels import topic_label_catalog

_SOURCE_LABELS = {
    "unknown": "Неизвестно",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "tgtrack": "TgTrack",
}

_MAX_SOURCE_LINES = 20


def _source_label(source: str) -> str:
    if source in _SOURCE_LABELS:
        return _SOURCE_LABELS[source]
    return source[:1].upper() + source[1:] if source else source


def _canonical_source(source: str) -> str:
    if source.lower().startswith("tgtrack"):
        return "tgtrack"
    return source


def _collapse_sources(users_by_first_source: dict[str, int]) -> dict[str, int]:
    collapsed: dict[str, int] = {}
    for source, count in users_by_first_source.items():
        key = _canonical_source(source)
        collapsed[key] = collapsed.get(key, 0) + count
    return collapsed


def _leads_label(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} заявка"
    if 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return f"{count} заявки"
    return f"{count} заявок"


def _format_topic_line(label: str, count: TopicCount) -> str:
    return f"  {label}: {count.unique_users} users ({count.taps} taps)"


def _topic_catalog(
    partner_types: Sequence[PartnerType],
) -> tuple[tuple[str, ...], dict[str, str]]:
    labels = topic_label_catalog(partner_types)
    partner_slugs = {t.slug for t in partner_types}
    order = tuple(t for t in TOPIC_ORDER if t not in partner_slugs) + tuple(
        t.slug for t in sorted(partner_types, key=lambda t: (t.sort_order, t.slug))
    )
    return order, labels


def _format_topic_section(
    title: str,
    topics: dict[str, TopicCount],
    *,
    topic_order: tuple[str, ...],
    topic_labels: dict[str, str],
) -> list[str]:
    lines = [title]
    known = set(topic_order)
    extra = tuple(sorted(t for t in topics if t not in known))
    ranked = sorted(
        topic_order + extra,
        key=lambda topic: (
            -topics.get(topic, TopicCount(0, 0)).unique_users,
            -topics.get(topic, TopicCount(0, 0)).taps,
            topic_labels.get(topic, topic),
        ),
    )
    for topic in ranked:
        count = topics.get(topic, TopicCount(0, 0))
        if count.taps == 0:
            continue
        lines.append(_format_topic_line(topic_labels.get(topic, topic), count))
    if len(lines) == 1:
        lines.append("  —")
    return lines


def _format_source_section(users_by_first_source: dict[str, int]) -> list[str]:
    lines = ["Источники:"]
    ranked = sorted(
        _collapse_sources(users_by_first_source).items(),
        key=lambda item: (-item[1], item[0]),
    )
    shown = ranked[:_MAX_SOURCE_LINES]
    rest = ranked[_MAX_SOURCE_LINES:]
    for source, count in shown:
        lines.append(f"  {_source_label(source)}: {count}")
    if rest:
        lines.append(f"  Другие: {sum(count for _, count in rest)}")
    if len(lines) == 1:
        lines.append("  —")
    return lines


def format_bot_stats(
    stats: BotStats,
    *,
    partner_types: Sequence[PartnerType] = (),
) -> str:
    topic_order, topic_labels = _topic_catalog(partner_types)

    real_estate_7d = stats.topics_7d.get(TOPIC_REAL_ESTATE, TopicCount(0, 0))
    real_estate_all = stats.topics_all_time.get(TOPIC_REAL_ESTATE, TopicCount(0, 0))

    topics_7d = {
        topic: count
        for topic, count in stats.topics_7d.items()
        if topic != TOPIC_REAL_ESTATE
    }
    topics_all_time = {
        topic: count
        for topic, count in stats.topics_all_time.items()
        if topic != TOPIC_REAL_ESTATE
    }

    lines = [
        "📊 Статистика бота",
        "",
        "Пользователи:",
        f"  Всего: {stats.total_users}",
        f"  Новые сегодня: {stats.new_users_today}",
        f"  Активны сегодня: {stats.active_today}",
        "",
        *_format_source_section(stats.users_by_first_source),
        "",
        "За 7 дней:",
        f"  Новые пользователи: {stats.new_users_7d}",
        "",
        *_format_topic_section(
            "Темы (7 дней):",
            topics_7d,
            topic_order=topic_order,
            topic_labels=topic_labels,
        ),
        "",
        *_format_topic_section(
            "Темы (всё время):",
            topics_all_time,
            topic_order=topic_order,
            topic_labels=topic_labels,
        ),
        "",
        "Недвижимость:",
        f"  За 7 дней: {real_estate_7d.unique_users} users ({real_estate_7d.taps} taps) → {_leads_label(stats.leads_7d)}",
        f"  Всё время: {real_estate_all.unique_users} users ({real_estate_all.taps} taps) → {_leads_label(stats.leads_all_time)}",
    ]
    return "\n".join(lines)
