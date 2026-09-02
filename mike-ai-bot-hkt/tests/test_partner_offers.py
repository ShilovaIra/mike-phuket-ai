from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from partner_dashboard.offers import wrap_partners_for_channel_user, wrap_partners_for_user
from partners import Partner


def _partner(**overrides) -> Partner:
    base = dict(
        id=uuid4(),
        name="Alpha FX",
        type="money_exchange",
        referral_url="https://t.me/alpha?start=ref",
        blurb="Обмен в Равае",
        sort_order=1,
        logo_path=None,
    )
    base.update(overrides)
    return Partner(**base)


@pytest.mark.asyncio
@pytest.mark.parametrize("public_base", ["", "   ", "/offers", "offers.example"])
async def test_wrap_keeps_original_urls_when_public_base_is_not_http(public_base):
    partner = _partner()

    wrapped = await wrap_partners_for_user(
        None, [partner], uuid4(), public_base=public_base
    )

    assert wrapped[0].referral_url == "https://t.me/alpha?start=ref"


@pytest.mark.asyncio
async def test_wrap_rewrites_when_public_base_is_https(monkeypatch):
    partner = _partner()

    async def fake_wrap(pool, *, partner, user_id):
        return "/r/test-token"

    monkeypatch.setattr("partner_dashboard.offers.wrap_offer_for_user", fake_wrap)

    wrapped = await wrap_partners_for_user(
        object(), [partner], uuid4(), public_base="https://offers.example/"
    )

    assert wrapped[0].referral_url == "https://offers.example/r/test-token"


@pytest.mark.asyncio
async def test_wrap_starts_conversation_when_tourist_never_sent_start(monkeypatch):
    started: list[str] = []

    class Store:
        pool = object()

        async def get_active_conversation(self, channel, external_id):
            return None

        async def start_conversation(self, channel, external_id, **kwargs):
            started.append(external_id)
            return SimpleNamespace(user_id=uuid4())

    async def fake_wrap(pool, partners, user_id, *, public_base):
        assert public_base == "https://offers.example"
        return ["wrapped"]

    monkeypatch.setattr("partner_dashboard.offers.wrap_partners_for_user", fake_wrap)

    wrapped = await wrap_partners_for_channel_user(
        Store(),
        [_partner()],
        "telegram",
        "9101",
        public_base="https://offers.example",
    )

    assert started == ["9101"]
    assert wrapped == ["wrapped"]


@pytest.mark.asyncio
async def test_channel_wrap_skips_conversation_when_public_base_is_not_http():
    class Store:
        pool = object()

        async def get_active_conversation(self, channel, external_id):
            raise AssertionError("must not look up conversation")

        async def start_conversation(self, channel, external_id, **kwargs):
            raise AssertionError("must not open a conversation")

    partner = _partner()
    wrapped = await wrap_partners_for_channel_user(
        Store(),
        [partner],
        "telegram",
        "9103",
        public_base="",
    )

    assert wrapped[0].referral_url == partner.referral_url


@pytest.mark.asyncio
async def test_wrap_reuses_active_conversation(monkeypatch):
    existing = SimpleNamespace(user_id=uuid4())

    class Store:
        pool = object()

        async def get_active_conversation(self, channel, external_id):
            return existing

        async def start_conversation(self, channel, external_id, **kwargs):
            raise AssertionError("must not open a new conversation")

    async def fake_wrap(pool, partners, user_id, *, public_base):
        assert user_id == existing.user_id
        return partners

    monkeypatch.setattr("partner_dashboard.offers.wrap_partners_for_user", fake_wrap)

    await wrap_partners_for_channel_user(
        Store(),
        [_partner()],
        "telegram",
        "9102",
        public_base="https://offers.example",
    )
