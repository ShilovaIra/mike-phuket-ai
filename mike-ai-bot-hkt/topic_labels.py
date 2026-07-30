"""Resolve analytics topic slugs to human-readable labels."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from db.store import TopicCount
from partners import PartnerType
from topics import TOPIC_LABELS

UNKNOWN_TOPIC_LABEL = "Без названия"


def topic_label_catalog(partner_types: Sequence[PartnerType]) -> dict[str, str]:
    partner_labels = {t.slug: t.topic_label for t in partner_types}
    return {**TOPIC_LABELS, **partner_labels}


def labeled_topic_rows(
    topics: Mapping[str, TopicCount],
    partner_types: Sequence[PartnerType] = (),
) -> list[dict[str, Any]]:
    labels = topic_label_catalog(partner_types)
    rows: list[dict[str, Any]] = []
    for slug, count in topics.items():
        rows.append(
            {
                "slug": slug,
                "label": labels.get(slug, UNKNOWN_TOPIC_LABEL),
                "unique_users": count.unique_users,
                "taps": count.taps,
            }
        )
    return rows
