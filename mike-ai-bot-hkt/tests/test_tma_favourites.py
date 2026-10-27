from __future__ import annotations

import pytest

from tests.conftest import requires_db
from tests.test_tma_chat import BOT_TOKEN, signed_init_data, tma_client, tma_headers


@pytest.fixture(autouse=True)
def _tma_env(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)


@requires_db
@pytest.mark.asyncio
async def test_signed_user_saves_a_visible_place_and_reads_it_back(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    place = await store.create_place(
        name="Якорная",
        category_id=beach.id,
        google_place_id="ChIJ_yakornaya",
        latitude=7.76,
        longitude=98.30,
        blurb="Закат",
        maps_url="https://maps.example/promthep",
        mike_recommends=True,
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        saved = await client.put(
            f"/api/tma/favourites/{place.id}",
            headers=tma_headers(),
            json={"saved": True},
        )
        listed = await client.get("/api/tma/favourites", headers=tma_headers())

    assert saved.status_code == 200
    assert saved.json() == {"saved": True}
    assert listed.status_code == 200
    assert listed.json() == [
        {
            "kind": "place",
            "id": str(place.id),
            "name": "Якорная",
            "category": "Пляж",
            "blurb": "Закат",
            "maps_url": "https://maps.example/promthep",
            "photo_url": "media/places/placeholder.jpg",
            "mike_recommends": True,
            "partner": None,
        }
    ]


@requires_db
@pytest.mark.asyncio
async def test_signed_user_saves_a_partner_ahead_of_an_older_place_and_can_remove_it(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    place = await store.create_place(
        name="Якорная",
        category_id=beach.id,
        google_place_id="ChIJ_partner_fav_place",
        latitude=7.76,
        longitude=98.30,
        blurb="Закат",
        maps_url="https://maps.example/partner-fav-place",
        mike_recommends=True,
    )
    partner = await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.test/money",
        blurb="Обмен на Бали",
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        headers = tma_headers()
        await client.put(
            f"/api/tma/favourites/{place.id}",
            headers=headers,
            json={"saved": True},
        )
        saved = await client.put(
            f"/api/tma/favourites/partners/{partner.id}",
            headers=headers,
            json={"saved": True},
        )
        listed = await client.get("/api/tma/favourites", headers=headers)
        removed = await client.put(
            f"/api/tma/favourites/partners/{partner.id}",
            headers=headers,
            json={"saved": False},
        )
        after = await client.get("/api/tma/favourites", headers=headers)

    assert saved.status_code == 200
    assert saved.json() == {"saved": True}
    body = listed.json()
    assert body[0] == {
        "kind": "partner",
        "id": str(partner.id),
        "name": "Money Shop",
        "type_label": "Обмен",
        "blurb": "Обмен на Бали",
        "logo_url": "",
    }
    assert body[1]["kind"] == "place"
    assert body[1]["id"] == str(place.id)
    assert body[1]["name"] == "Якорная"
    assert removed.status_code == 200
    assert removed.json() == {"saved": False}
    assert [item["kind"] for item in after.json()] == ["place"]
    assert [item["id"] for item in after.json()] == [str(place.id)]


@requires_db
@pytest.mark.asyncio
async def test_inactive_partner_is_left_out_of_favourites_until_it_returns(store):
    partner = await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.test/money-hidden",
        blurb="Обмен на Бали",
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        headers = tma_headers()
        await client.put(
            f"/api/tma/favourites/partners/{partner.id}",
            headers=headers,
            json={"saved": True},
        )
        await store.update_partner(
            partner.id,
            name=partner.name,
            type=partner.type,
            referral_url=partner.referral_url,
            blurb=partner.blurb or "",
            is_active=False,
            sort_order=partner.sort_order,
        )
        hidden = await client.get("/api/tma/favourites", headers=headers)
        await store.update_partner(
            partner.id,
            name=partner.name,
            type=partner.type,
            referral_url=partner.referral_url,
            blurb=partner.blurb or "",
            is_active=True,
            sort_order=partner.sort_order,
        )
        restored = await client.get("/api/tma/favourites", headers=headers)

    assert hidden.json() == []
    assert [item["id"] for item in restored.json()] == [str(partner.id)]
    assert restored.json()[0]["kind"] == "partner"


@requires_db
@pytest.mark.asyncio
async def test_saving_twice_keeps_one_entry_and_turning_it_off_removes_it(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    place = await store.create_place(
        name="Якорная",
        category_id=beach.id,
        google_place_id="ChIJ_yakornaya_toggle",
        latitude=7.76,
        longitude=98.30,
        maps_url="https://maps.example/toggle",
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        headers = tma_headers()
        first = await client.put(
            f"/api/tma/favourites/{place.id}",
            headers=headers,
            json={"saved": True},
        )
        second = await client.put(
            f"/api/tma/favourites/{place.id}",
            headers=headers,
            json={"saved": True},
        )
        listed = await client.get("/api/tma/favourites", headers=headers)
        removed = await client.put(
            f"/api/tma/favourites/{place.id}",
            headers=headers,
            json={"saved": False},
        )
        after = await client.get("/api/tma/favourites", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == {"saved": True}
    assert [item["id"] for item in listed.json()] == [str(place.id)]
    assert removed.status_code == 200
    assert removed.json() == {"saved": False}
    assert after.json() == []


@requires_db
@pytest.mark.asyncio
async def test_newer_save_is_listed_first(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    older = await store.create_place(
        name="Якорная",
        category_id=beach.id,
        google_place_id="ChIJ_older",
        latitude=7.76,
        longitude=98.30,
        maps_url="https://maps.example/older",
    )
    newer = await store.create_place(
        name="Анапа",
        category_id=beach.id,
        google_place_id="ChIJ_newer",
        latitude=7.77,
        longitude=98.31,
        maps_url="https://maps.example/newer",
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        headers = tma_headers()
        await client.put(
            f"/api/tma/favourites/{older.id}",
            headers=headers,
            json={"saved": True},
        )
        await client.put(
            f"/api/tma/favourites/{newer.id}",
            headers=headers,
            json={"saved": True},
        )
        listed = await client.get("/api/tma/favourites", headers=headers)

    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()] == ["Анапа", "Якорная"]


@requires_db
@pytest.mark.asyncio
async def test_hidden_place_stays_saved_and_returns_in_the_same_order(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    shop = next(
        category for category in await store.list_place_categories() if category.slug == "shop"
    )
    partner = await store.create_partner(
        name="Money Shop",
        type="money_exchange",
        referral_url="https://example.test/money",
    )
    shore = await store.create_place(
        name="Якорная",
        category_id=beach.id,
        google_place_id="ChIJ_shore",
        latitude=7.76,
        longitude=98.30,
        maps_url="https://maps.example/shore",
    )
    office = await store.create_place(
        name="Касса",
        category_id=shop.id,
        partner_id=partner.id,
        google_place_id="ChIJ_office",
        latitude=7.82,
        longitude=98.30,
        maps_url="https://maps.example/office",
    )

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        headers = tma_headers()
        await client.put(
            f"/api/tma/favourites/{shore.id}",
            headers=headers,
            json={"saved": True},
        )
        await client.put(
            f"/api/tma/favourites/{office.id}",
            headers=headers,
            json={"saved": True},
        )
        await store.update_place(
            shore.id,
            name=shore.name,
            category_id=shore.category_id,
            google_place_id=shore.google_place_id,
            latitude=shore.latitude,
            longitude=shore.longitude,
            maps_url=shore.maps_url,
            is_active=False,
        )
        hidden_place = await client.get("/api/tma/favourites", headers=headers)
        await store.update_place(
            shore.id,
            name=shore.name,
            category_id=shore.category_id,
            google_place_id=shore.google_place_id,
            latitude=shore.latitude,
            longitude=shore.longitude,
            maps_url=shore.maps_url,
            is_active=True,
        )
        await store.update_partner(
            partner.id,
            name=partner.name,
            type=partner.type,
            referral_url=partner.referral_url,
            blurb=partner.blurb or "",
            is_active=False,
            sort_order=partner.sort_order,
        )
        hidden_partner = await client.get("/api/tma/favourites", headers=headers)
        await store.update_partner(
            partner.id,
            name=partner.name,
            type=partner.type,
            referral_url=partner.referral_url,
            blurb=partner.blurb or "",
            is_active=True,
            sort_order=partner.sort_order,
        )
        restored = await client.get("/api/tma/favourites", headers=headers)

    assert [item["name"] for item in hidden_place.json()] == ["Касса"]
    assert [item["name"] for item in hidden_partner.json()] == ["Якорная"]
    assert [item["name"] for item in restored.json()] == ["Касса", "Якорная"]


@requires_db
@pytest.mark.asyncio
async def test_bad_or_missing_signature_cannot_open_list_or_save(store):
    beach = next(
        category for category in await store.list_place_categories() if category.slug == "beach"
    )
    place = await store.create_place(
        name="Якорная",
        category_id=beach.id,
        google_place_id="ChIJ_auth",
        latitude=7.76,
        longitude=98.30,
        maps_url="https://maps.example/auth",
    )
    forged = signed_init_data().replace("hash=", "hash=00", 1)

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        forged_session = await client.post(
            "/api/tma/session",
            headers={"Authorization": f"tma {forged}"},
        )
        missing_session = await client.post("/api/tma/session")
        forged_list = await client.get(
            "/api/tma/favourites",
            headers={"Authorization": f"tma {forged}"},
        )
        missing_list = await client.get("/api/tma/favourites")
        forged_save = await client.put(
            f"/api/tma/favourites/{place.id}",
            headers={"Authorization": f"tma {forged}"},
            json={"saved": True},
        )
        missing_save = await client.put(
            f"/api/tma/favourites/{place.id}",
            json={"saved": True},
        )
        listed = await client.get("/api/tma/favourites", headers=tma_headers())

    assert forged_session.status_code == 401
    assert missing_session.status_code == 401
    assert forged_list.status_code == 401
    assert missing_list.status_code == 401
    assert forged_save.status_code == 401
    assert missing_save.status_code == 401
    assert listed.status_code == 200
    assert listed.json() == []


@requires_db
@pytest.mark.asyncio
async def test_opening_a_session_records_the_user_and_leaves_the_chat_empty(store):
    await store.create_admin_user(email="admin@example.com", password="admin123")

    async def model(_messages):
        raise AssertionError("model should not run")

    async with tma_client(store, model) as client:
        opened = await client.post("/api/tma/session", headers=tma_headers())
        history = await client.get("/api/tma/messages", headers=tma_headers())
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        stats = await client.get(
            "/api/stats",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

    assert opened.status_code == 204
    assert history.status_code == 200
    assert history.json()["messages"] == []
    assert stats.json()["total_users"] == 1
    assert stats.json()["users_by_first_source"] == {"tma": 1}
