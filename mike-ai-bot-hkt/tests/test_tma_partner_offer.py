from __future__ import annotations

import pytest

from tests.conftest import requires_db
from tests.test_tma_chat import BOT_TOKEN, tma_client, tma_headers


@pytest.fixture(autouse=True)
def _tma_env(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    monkeypatch.setenv("PARTNER_OFFER_BASE_URL", "https://partners.example")


@requires_db
@pytest.mark.asyncio
async def test_partner_offer_is_a_tracked_link_with_the_bot_button_label(store):
    partner = await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.test/money",
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        response = await client.post(
            f"/api/tma/partners/{partner.id}/offer",
            headers=tma_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "Обменять с Money Shop"
    assert body["url"].startswith("https://partners.example/r/")
    assert "example.test/money" not in body["url"]
    assert "referral_url" not in body
