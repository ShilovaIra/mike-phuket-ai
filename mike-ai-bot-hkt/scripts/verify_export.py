#!/usr/bin/env python3
"""
Verify a RAM export file before stopping the bot or starting migration.

Usage:
  python3 scripts/verify_export.py /tmp/mike_sessions_export.json
  python3 scripts/verify_export.py /tmp/mike_sessions_export.json --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def verify(path: Path, strict: bool) -> int:
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: invalid JSON: {exc}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    for key in ("exported_at", "session_count", "sessions"):
        if key not in data:
            errors.append(f"missing top-level key: {key}")

    sessions = data.get("sessions", {})
    if not isinstance(sessions, dict):
        errors.append("sessions must be an object")
        sessions = {}

    if data.get("session_count") != len(sessions):
        warnings.append(
            f"session_count ({data.get('session_count')}) != len(sessions) ({len(sessions)})"
        )

    active = 0
    with_history = 0
    leads_sent = 0

    for user_id, session in sessions.items():
        if not isinstance(session, dict):
            errors.append(f"session {user_id}: not an object")
            continue

        history = session.get("history", [])
        if not isinstance(history, list):
            errors.append(f"session {user_id}: history must be a list")
            continue

        if history:
            with_history += 1
            active += 1

        if session.get("lead_sent"):
            leads_sent += 1

        for msg in history:
            if not isinstance(msg, dict):
                errors.append(f"session {user_id}: history item not an object")
                break
            if "role" not in msg or "content" not in msg:
                errors.append(f"session {user_id}: history item missing role/content")
                break

    print(f"File:           {path}")
    print(f"Exported at:    {data.get('exported_at', '?')}")
    print(f"Source PID:     {data.get('pid', '?')}")
    print(f"Sessions:       {len(sessions)}")
    print(f"With history:   {with_history}")
    print(f"Leads sent:     {leads_sent}")
    print(f"Total messages: {data.get('total_messages', sum(len(s.get('history', [])) for s in sessions.values()))}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nFAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1

    if strict and len(sessions) == 0:
        print("\nFAIL (--strict): zero sessions exported")
        return 1

    print("\nPASS: export file is valid")
    print("\nSafe to proceed ONLY after you also:")
    print("  1. scp this file off the server")
    print("  2. Re-run export once more and confirm counts match")
    print("  3. THEN stop the old bot for cutover")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify mike bot RAM export JSON")
    parser.add_argument("path", type=Path, help="Path to mike_sessions_export.json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if session_count is 0 (use when you know users are active)",
    )
    args = parser.parse_args()
    sys.exit(verify(args.path, args.strict))


if __name__ == "__main__":
    main()
