from __future__ import annotations

from uuid import UUID

import asyncpg
import pytest

from tests.conftest import requires_db


@requires_db
async def test_list_place_categories_returns_seeded_kinds(store):
    categories = await store.list_place_categories()

    assert [(category.slug, category.label) for category in categories] == [
        ("cafe", "Кафе"),
        ("restaurant", "Ресторан"),
        ("bar", "Бар"),
        ("beach", "Пляж"),
        ("shop", "Магазин"),
    ]
    assert all(isinstance(category.id, UUID) for category in categories)


@requires_db
async def test_create_place_round_trips_category_partner_and_coordinates(store):
    categories = await store.list_place_categories()
    shop = next(category for category in categories if category.slug == "shop")
    beach = next(category for category in categories if category.slug == "beach")
    partner = await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.test/money",
    )

    office = await store.create_place(
        name="Money Shop Kata",
        category_id=shop.id,
        partner_id=partner.id,
        google_place_id="ChIJ_office",
        latitude=7.82,
        longitude=98.30,
        blurb="Офис на Кате",
    )
    shore = await store.create_place(
        name="Kata Beach",
        category_id=beach.id,
        google_place_id="ChIJ_beach",
        latitude=7.81,
        longitude=98.29,
    )

    visible = {place.name: place for place in await store.list_visible_places()}

    assert visible["Money Shop Kata"].id == office.id
    assert visible["Money Shop Kata"].category_id == shop.id
    assert visible["Money Shop Kata"].partner_id == partner.id
    assert visible["Money Shop Kata"].google_place_id == "ChIJ_office"
    assert visible["Money Shop Kata"].latitude == pytest.approx(7.82)
    assert visible["Money Shop Kata"].longitude == pytest.approx(98.30)
    assert visible["Money Shop Kata"].blurb == "Офис на Кате"
    assert visible["Kata Beach"].id == shore.id
    assert visible["Kata Beach"].partner_id is None
    assert visible["Kata Beach"].blurb is None


@requires_db
async def test_create_place_rejects_duplicate_google_place_id(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    await store.create_place(
        name="Kata",
        category_id=beach.id,
        google_place_id="ChIJ_same",
        latitude=7.8,
        longitude=98.3,
    )

    with pytest.raises(asyncpg.UniqueViolationError):
        await store.create_place(
            name="Kata again",
            category_id=beach.id,
            google_place_id="ChIJ_same",
            latitude=7.81,
            longitude=98.31,
        )


async def _set_partner_active(store, partner, *, is_active: bool):
    return await store.update_partner(
        partner.id,
        name=partner.name,
        type=partner.type,
        referral_url=partner.referral_url,
        blurb=partner.blurb or "",
        is_active=is_active,
        sort_order=partner.sort_order,
    )


@requires_db
async def test_visible_places_follow_place_and_partner_flags(store):
    categories = await store.list_place_categories()
    beach = next(category for category in categories if category.slug == "beach")
    shop = next(category for category in categories if category.slug == "shop")
    partner = await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.test/money",
    )
    await store.create_place(
        name="Kata Beach",
        category_id=beach.id,
        google_place_id="ChIJ_kata",
        latitude=7.8,
        longitude=98.3,
    )
    await store.create_place(
        name="Secret Beach",
        category_id=beach.id,
        google_place_id="ChIJ_secret",
        latitude=7.7,
        longitude=98.2,
        is_active=False,
    )
    await store.create_place(
        name="Money Shop Kata",
        category_id=shop.id,
        partner_id=partner.id,
        google_place_id="ChIJ_kata_office",
        latitude=7.82,
        longitude=98.30,
    )
    await store.create_place(
        name="Closed Office",
        category_id=shop.id,
        partner_id=partner.id,
        google_place_id="ChIJ_closed_office",
        latitude=7.83,
        longitude=98.31,
        is_active=False,
    )

    def names():
        return store.list_visible_places()

    assert {place.name for place in await names()} == {"Kata Beach", "Money Shop Kata"}

    await _set_partner_active(store, partner, is_active=False)
    assert {place.name for place in await names()} == {"Kata Beach"}

    await _set_partner_active(store, partner, is_active=True)
    assert {place.name for place in await names()} == {"Kata Beach", "Money Shop Kata"}


@requires_db
async def test_place_assets_return_storage_keys_in_sort_order(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    place = await store.create_place(
        name="Kata Beach",
        category_id=beach.id,
        google_place_id="ChIJ_kata_photos",
        latitude=7.8,
        longitude=98.3,
    )
    await store.add_place_asset(place.id, "places/kata/second.jpg", sort_order=2)
    await store.add_place_asset(place.id, "places/kata/first.jpg", sort_order=1)

    assets = await store.list_place_assets(place.id)

    assert [asset.path for asset in assets] == [
        "places/kata/first.jpg",
        "places/kata/second.jpg",
    ]
    assert all(isinstance(asset.id, UUID) for asset in assets)
    assert {asset.place_id for asset in assets} == {place.id}
