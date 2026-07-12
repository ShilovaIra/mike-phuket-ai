from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from db.store import SessionStore


def select_sessions(
    sessions: dict[str, Any],
    *,
    fraction: float = 1.0,
) -> dict[str, Any]:
    """Deterministically take the first N sessions by sorted user id."""
    if fraction >= 1.0:
        return sessions
    if fraction <= 0:
        return {}

    keys = sorted(sessions.keys())
    take = max(1, int(len(keys) * fraction)) if keys else 0
    chosen = keys[:take]
    return {key: sessions[key] for key in chosen}


def load_export_sessions(
    path: Path,
    *,
    fraction: float = 1.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (selected_sessions, meta) from an export JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    sessions: dict[str, Any] = data.get("sessions", {})
    if not isinstance(sessions, dict):
        raise ValueError("export sessions must be an object")

    selected = select_sessions(sessions, fraction=fraction)
    meta = {
        "exported_at": data.get("exported_at"),
        "source_session_count": len(sessions),
        "selected_session_count": len(selected),
        "fraction": fraction,
    }
    return selected, meta


def write_export_subset(
    source_path: Path,
    dest_path: Path,
    *,
    fraction: float = 0.5,
) -> dict[str, Any]:
    """Write a smaller export JSON (for scp / staging seed). Not for git."""
    selected, meta = load_export_sessions(source_path, fraction=fraction)
    payload = {
        "exported_at": meta["exported_at"],
        "pid": None,
        "session_count": len(selected),
        "total_messages": sum(len(s.get("history", [])) for s in selected.values()),
        "sessions": selected,
        "subset": {
            "fraction": fraction,
            "source_session_count": meta["source_session_count"],
            "purpose": "staging_seed",
        },
    }
    dest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**meta, "total_messages": payload["total_messages"], "dest": str(dest_path)}


async def import_from_export(
    store: SessionStore,
    path: Path,
    *,
    fraction: float = 1.0,
) -> dict[str, int]:
    sessions, meta = load_export_sessions(path, fraction=fraction)

    stats = {
        "users": 0,
        "conversations": 0,
        "messages": 0,
        "leads": 0,
        "skipped_empty": 0,
        "source_sessions": meta["source_session_count"],
        "selected_sessions": meta["selected_session_count"],
    }

    for external_id, session in sessions.items():
        if not isinstance(session, dict):
            continue

        history = session.get("history", [])
        if not history:
            stats["skipped_empty"] += 1
            continue

        source = session.get("source", "unknown") or "unknown"
        await store.start_conversation("telegram", external_id, source=source)
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
