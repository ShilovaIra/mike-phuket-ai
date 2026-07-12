from __future__ import annotations

import json
from pathlib import Path

import pytest

from db.import_sessions import import_from_export
from tests.conftest import requires_db


@requires_db
async def test_import_restores_message_history_from_export(store, tmp_path: Path):
    export = {
        "sessions": {
            "999001": {
                "source": "instagram",
                "history": [
                    {"role": "user", "content": "Привет"},
                    {"role": "assistant", "content": "Привет! Чем помочь?"},
                ],
                "lead_sent": False,
            }
        }
    }
    path = tmp_path / "export.json"
    path.write_text(json.dumps(export), encoding="utf-8")

    stats = await import_from_export(store, path)

    assert stats["messages"] == 2
    assert await store.get_ai_context("telegram", "999001") == [
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "Привет! Чем помочь?"},
    ]

    active = await store.get_active_conversation("telegram", "999001")
    assert active is not None
    assert active.source == "instagram"
