from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from db.store import SessionStore


async def import_from_export(store: SessionStore, path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    sessions: dict[str, Any] = data.get("sessions", {})

    stats = {
        "users": 0,
        "conversations": 0,
        "messages": 0,
        "leads": 0,
        "skipped_empty": 0,
    }

    for external_id, session in sessions.items():
        if not isinstance(session, dict):
            continue

        history = session.get("history", [])
        if not history:
            stats["skipped_empty"] += 1
            continue

        source = session.get("source", "unknown") or "unknown"
        ctx = await store.start_conversation("telegram", external_id, source=source)
        stats["users"] += 1
        stats["conversations"] += 1

        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role not in ("user", "assistant") or not isinstance(content, str):
                continue
            await store.append_message(
                "telegram",
                external_id,
                role=role,
                content=content,
            )
            stats["messages"] += 1

        if session.get("lead_sent"):
            lead = await store.create_lead(
                "telegram",
                external_id,
                snapshot={"imported": True, "telegram_id": external_id},
            )
            if lead and lead.created:
                stats["leads"] += 1

    return stats
