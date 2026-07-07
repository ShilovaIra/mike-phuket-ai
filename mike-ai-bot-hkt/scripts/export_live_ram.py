"""
Dump in-memory PTB user sessions from a RUNNING bot process.

Run via process injection while bot.py is still polling — do NOT restart first.

  sudo pyrasite <PID> scripts/export_live_ram.py
  # or: scripts/export_via_gdb.sh <PID>

Output: /tmp/mike_sessions_export.json (override with MIKE_EXPORT_PATH)
"""

from __future__ import annotations

import gc
import json
import os
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path(os.environ.get("MIKE_EXPORT_PATH", "/tmp/mike_sessions_export.json"))


def find_application():
    for obj in gc.get_objects():
        cls = obj.__class__
        if cls.__name__ != "Application":
            continue
        module = getattr(cls, "__module__", "")
        if not module.startswith("telegram.ext"):
            continue
        if hasattr(obj, "user_data"):
            return obj
    return None


def serialize_user_data(raw: dict) -> dict:
    return {
        "source": raw.get("source", "unknown"),
        "history": raw.get("history", []),
        "lead_sent": bool(raw.get("lead_sent", False)),
    }


def main() -> None:
    app = find_application()
    if app is None:
        raise SystemExit(
            "ERROR: telegram.ext.Application not found in this process. "
            "Is this the bot PID? Is bot.py still running?"
        )

    sessions: dict[str, dict] = {}
    user_data = app.user_data

    try:
        items = user_data.items()
    except AttributeError:
        items = dict(user_data).items()

    for user_id, data in items:
        if not isinstance(data, dict):
            continue
        sessions[str(user_id)] = serialize_user_data(data)

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "session_count": len(sessions),
        "total_messages": sum(len(s.get("history", [])) for s in sessions.values()),
        "sessions": sessions,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: exported {len(sessions)} sessions -> {OUTPUT}")
    print(f"    total history messages: {payload['total_messages']}")


if __name__ == "__main__":
    main()
