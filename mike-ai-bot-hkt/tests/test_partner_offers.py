from __future__ import annotations

from uuid import uuid4

import pytest

from partner_dashboard.offers import wrap_partners_for_user
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
