from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import requires_db
from tests.test_tma_chat import BOT_TOKEN, signed_init_data, tma_headers


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


@asynccontextmanager
async def operator_client(store, *, partner_name: str = "Money Shop"):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    partner = await store.create_partner(
        name=partner_name,
        type="money_exchange",
        referral_url="https://example.com/money",
    )
    app = create_app(store=store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        yield client, partner


async def create_shop_user(client, partner_id, *, email: str = "shop@example.com") -> str:
    created = await client.post(
        "/api/partner-users",
        json={
            "email": email,
            "password": "shop-secret",
            "partner_ids": [str(partner_id)],
        },
    )
    assert created.status_code == 201
    login = await client.post(
        "/api/partner/auth/login",
        json={"email": email, "password": "shop-secret"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


@requires_db
@pytest.mark.asyncio
async def test_operator_creates_partner_user_who_sees_zero_stats_for_that_partner(store):
    async with operator_client(store) as (client, partner):
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id)],
            },
        )
        assert created.status_code == 201
        assert created.json()["email"] == "shop@example.com"

        partner_login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )
        assert partner_login.status_code == 200
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {partner_login.json()['access_token']}"},
        )

    assert stats.status_code == 200
    body = stats.json()
    assert body["partner_id"] == str(partner.id)
    zeros = {"views": 0, "referral_clicks": 0, "opened_views": 0}
    assert body["all_time"] == zeros
    assert body["last_30_days"] == zeros
    assert body["map_opens"] == 0


@requires_db
@pytest.mark.asyncio
async def test_partner_user_login_with_wrong_password_returns_401(store):
    async with operator_client(store) as (client, partner):
        await create_shop_user(client, partner.id)
        response = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "wrong"},
        )

    assert response.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_operator_token_cannot_read_partner_stats(store):
    async with operator_client(store) as (client, partner):
        response = await client.get(f"/api/partner/stats?partner_id={partner.id}")

    assert response.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_partner_user_token_cannot_read_operator_stats(store):
    async with operator_client(store) as (client, partner):
        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            "/api/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        partners = await client.get(
            "/api/partners",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats.status_code == 401
    assert partners.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_create_partner_user_without_access_is_rejected(store):
    async with operator_client(store) as (client, _partner):
        response = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [],
            },
        )

    assert response.status_code == 422


@requires_db
@pytest.mark.asyncio
async def test_create_partner_user_with_operator_email_is_rejected(store):
    async with operator_client(store) as (client, partner):
        response = await client.post(
            "/api/partner-users",
            json={
                "email": "admin@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id)],
            },
        )

    assert response.status_code == 409


@requires_db
@pytest.mark.asyncio
async def test_partner_user_me_lists_partners_they_can_access(store):
    async with operator_client(store) as (client, first):
        other = await store.create_partner(
            name="Ex24",
            type="money_exchange",
            referral_url="https://example.com/ex24",
        )
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(first.id), str(other.id)],
            },
        )
        assert created.status_code == 201
        login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )
        me = await client.get(
            "/api/partner/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )

    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "shop@example.com"
    names = {p["name"]: p["id"] for p in body["partners"]}
    assert names["Money Shop"] == str(first.id)
    assert names["Ex24"] == str(other.id)


@requires_db
@pytest.mark.asyncio
async def test_partner_user_cannot_read_stats_for_partner_without_access(store):
    async with operator_client(store) as (client, first):
        other = await store.create_partner(
            name="Ex24",
            type="money_exchange",
            referral_url="https://example.com/ex24",
        )
        token = await create_shop_user(client, first.id)
        response = await client.get(
            f"/api/partner/stats?partner_id={other.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


@requires_db
@pytest.mark.asyncio
async def test_deleted_partner_user_cannot_sign_in(store):
    async with operator_client(store) as (client, partner):
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id)],
            },
        )
        user_id = created.json()["id"]
        deleted = await client.delete(f"/api/partner-users/{user_id}")
        assert deleted.status_code == 204
        login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )

    assert login.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_partner_user_cannot_sign_in_after_last_access_revoked(store):
    async with operator_client(store) as (client, partner):
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id)],
            },
        )
        user_id = created.json()["id"]
        patched = await client.patch(
            f"/api/partner-users/{user_id}",
            json={"partner_ids": []},
        )
        assert patched.status_code == 200
        login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )

    assert login.status_code == 401


@requires_db
@pytest.mark.asyncio
async def test_unlisted_partner_still_returns_stats(store):
    async with operator_client(store) as (client, partner):
        await store.update_partner(
            partner.id,
            name=partner.name,
            type=partner.type,
            referral_url=partner.referral_url,
            blurb=partner.blurb or "",
            is_active=False,
            sort_order=partner.sort_order,
        )
        token = await create_shop_user(client, partner.id)
        response = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["partner_id"] == str(partner.id)


@requires_db
@pytest.mark.asyncio
async def test_wrapped_offer_redirects_to_partner_referral_url(store):
    from partner_dashboard.offers import wrap_offer_for_user

    async with operator_client(store) as (client, partner):
        ctx = await store.start_conversation("telegram", "9001")
        path = await wrap_offer_for_user(
            store.pool, partner=partner, user_id=ctx.user_id
        )
        assert path.startswith("/r/")
        response = await client.get(path, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == partner.referral_url


@requires_db
@pytest.mark.asyncio
async def test_wrap_click_counts_as_view_click_and_opened_view(store):
    from partner_dashboard.offers import wrap_offer_for_user

    async with operator_client(store) as (client, partner):
        ctx = await store.start_conversation("telegram", "9002")
        path = await wrap_offer_for_user(
            store.pool, partner=partner, user_id=ctx.user_id
        )
        await client.get(path, follow_redirects=False)
        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats.status_code == 200
    body = stats.json()
    assert body["all_time"] == {"views": 1, "referral_clicks": 1, "opened_views": 1}
    assert body["last_30_days"] == {"views": 1, "referral_clicks": 1, "opened_views": 1}


@requires_db
@pytest.mark.asyncio
async def test_second_tap_on_same_showing_counts_click_not_opened_view(store):
    from partner_dashboard.offers import wrap_offer_for_user

    async with operator_client(store) as (client, partner):
        ctx = await store.start_conversation("telegram", "9003")
        path = await wrap_offer_for_user(
            store.pool, partner=partner, user_id=ctx.user_id
        )
        await client.get(path, follow_redirects=False)
        await client.get(path, follow_redirects=False)
        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats.json()["all_time"] == {
        "views": 1,
        "referral_clicks": 2,
        "opened_views": 1,
    }


@requires_db
@pytest.mark.asyncio
async def test_last_30_days_excludes_events_older_than_30_days(store):
    from partner_dashboard.offers import wrap_offer_for_user

    async with operator_client(store) as (client, partner):
        ctx = await store.start_conversation("telegram", "9004")
        path = await wrap_offer_for_user(
            store.pool, partner=partner, user_id=ctx.user_id
        )
        await client.get(path, follow_redirects=False)
        async with store.pool.acquire() as conn:
            await conn.execute(
                "UPDATE partner_views SET created_at = now() - interval '40 days'"
            )
            await conn.execute(
                "UPDATE partner_referral_clicks SET created_at = now() - interval '40 days'"
            )
        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    body = stats.json()
    assert body["all_time"] == {"views": 1, "referral_clicks": 1, "opened_views": 1}
    assert body["last_30_days"] == {"views": 0, "referral_clicks": 0, "opened_views": 0}


@requires_db
@pytest.mark.asyncio
async def test_stats_do_not_include_another_partners_views(store):
    from partner_dashboard.offers import wrap_offer_for_user

    async with operator_client(store) as (client, first):
        other = await store.create_partner(
            name="Ex24",
            type="money_exchange",
            referral_url="https://example.com/ex24",
        )
        ctx = await store.start_conversation("telegram", "9005")
        path = await wrap_offer_for_user(
            store.pool, partner=other, user_id=ctx.user_id
        )
        await client.get(path, follow_redirects=False)
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(first.id), str(other.id)],
            },
        )
        assert created.status_code == 201
        login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )
        token = login.json()["access_token"]
        first_stats = await client.get(
            f"/api/partner/stats?partner_id={first.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        other_stats = await client.get(
            f"/api/partner/stats?partner_id={other.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first_stats.json()["all_time"]["views"] == 0
    assert other_stats.json()["all_time"]["views"] == 1


@requires_db
@pytest.mark.asyncio
async def test_wrap_partners_for_user_rewrites_offer_urls(store):
    from partner_dashboard.offers import wrap_partners_for_user

    async with operator_client(store) as (client, partner):
        ctx = await store.start_conversation("telegram", "9006")
        wrapped = await wrap_partners_for_user(
            store.pool,
            [partner],
            ctx.user_id,
            public_base="https://offers.example",
        )
        assert wrapped[0].referral_url.startswith("https://offers.example/r/")
        path = wrapped[0].referral_url.removeprefix("https://offers.example")
        response = await client.get(path, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/money"


@requires_db
@pytest.mark.asyncio
async def test_operator_lists_partner_users(store):
    async with operator_client(store) as (client, partner):
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id)],
            },
        )
        listed = await client.get("/api/partner-users")

    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["id"] == created.json()["id"]
    assert rows[0]["email"] == "shop@example.com"
    assert datetime.fromisoformat(rows[0]["created_at"]).tzinfo is not None
    assert rows[0]["partners"][0]["id"] == str(partner.id)
    assert rows[0]["partners"][0]["name"] == "Money Shop"


@requires_db
@pytest.mark.asyncio
async def test_operator_can_reset_partner_user_password(store):
    async with operator_client(store) as (client, partner):
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id)],
            },
        )
        patched = await client.patch(
            f"/api/partner-users/{created.json()['id']}",
            json={"password": "new-secret"},
        )
        assert patched.status_code == 200
        old_login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )
        new_login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "new-secret"},
        )

    assert old_login.status_code == 401
    assert new_login.status_code == 200


@requires_db
@pytest.mark.asyncio
async def test_partner_stats_count_distinct_users_who_chose_that_category(store):
    async with operator_client(store) as (client, partner):
        await store.start_conversation("telegram", "9101", source="unknown")
        await store.record_topic_event("telegram", "9101", topic="money_exchange")
        async with store.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE topic_events
                SET created_at = now() - interval '40 days'
                WHERE topic = 'money_exchange'
                """
            )
        await store.start_conversation("telegram", "9102", source="unknown")
        await store.record_topic_event("telegram", "9102", topic="money_exchange")
        await store.record_topic_event("telegram", "9102", topic="money_exchange")
        await store.start_conversation("telegram", "9103", source="unknown")
        await store.record_topic_event("telegram", "9103", topic="vehicle_rental")

        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats.status_code == 200
    assert stats.json()["category_users"] == {
        "phrase": "обмен рублей",
        "all_time": 2,
        "last_30_days": 1,
    }


@requires_db
@pytest.mark.asyncio
async def test_partners_of_the_same_category_see_the_same_user_counts(store):
    async with operator_client(store) as (client, first):
        other = await store.create_partner(
            name="Ex24",
            type="money_exchange",
            referral_url="https://example.com/ex24",
        )
        await store.start_conversation("telegram", "9201", source="unknown")
        await store.record_topic_event("telegram", "9201", topic="money_exchange")
        created = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(first.id), str(other.id)],
            },
        )
        assert created.status_code == 201
        login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )
        token = login.json()["access_token"]
        first_stats = await client.get(
            f"/api/partner/stats?partner_id={first.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        other_stats = await client.get(
            f"/api/partner/stats?partner_id={other.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first_stats.json()["category_users"] == {
        "phrase": "обмен рублей",
        "all_time": 1,
        "last_30_days": 1,
    }
    assert other_stats.json()["category_users"] == first_stats.json()["category_users"]


@requires_db
@pytest.mark.asyncio
async def test_updated_choice_phrase_shows_on_partner_stats(store):
    async with operator_client(store) as (client, partner):
        updated = await client.patch(
            "/api/partner-types/money_exchange",
            json={
                "slug": "money_exchange",
                "is_menu_visible": True,
                "sort_order": 10,
                "button_label": "Обмен",
                "topic_label": "Обмен",
                "intro": "intro",
                "fallback": "fallback",
                "caption_emoji": "💰",
                "caption_cta": "cta",
                "button_template": "кнопка {name}",
                "choice_phrase": "обмен валюты",
            },
        )
        assert updated.status_code == 200
        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats.status_code == 200
    assert stats.json()["category_users"]["phrase"] == "обмен валюты"


@requires_db
@pytest.mark.asyncio
async def test_partner_stats_count_tourists_who_saved_the_current_partner(store, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    async with operator_client(store) as (client, partner):
        other = await store.create_partner(
            name="Ex24",
            type="money_exchange",
            referral_url="https://example.com/ex24",
        )
        for user_id in (101, 102):
            saved = await client.put(
                f"/api/tma/favourites/partners/{partner.id}",
                headers=tma_headers(signed_init_data(user_id=user_id)),
                json={"saved": True},
            )
            assert saved.status_code == 200
        other_saved = await client.put(
            f"/api/tma/favourites/partners/{other.id}",
            headers=tma_headers(signed_init_data(user_id=103)),
            json={"saved": True},
        )
        assert other_saved.status_code == 200
        token = await create_shop_user(client, partner.id)
        stats = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats.status_code == 200
    assert stats.json()["favourite_users"] == 2


@requires_db
@pytest.mark.asyncio
async def test_partner_stats_drop_a_tourist_who_removes_the_current_partner(store, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    async with operator_client(store) as (client, partner):
        headers = tma_headers(signed_init_data(user_id=201))
        saved = await client.put(
            f"/api/tma/favourites/partners/{partner.id}",
            headers=headers,
            json={"saved": True},
        )
        assert saved.status_code == 200
        token = await create_shop_user(client, partner.id)
        before = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        removed = await client.put(
            f"/api/tma/favourites/partners/{partner.id}",
            headers=headers,
            json={"saved": False},
        )
        assert removed.status_code == 200
        after = await client.get(
            f"/api/partner/stats?partner_id={partner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert before.status_code == 200
    assert before.json()["favourite_users"] == 1
    assert after.status_code == 200
    assert after.json()["favourite_users"] == 0


@requires_db
@pytest.mark.asyncio
async def test_map_open_counts_for_the_partner_who_owns_the_place_at_the_tap(store):
    from tests.test_admin_api_places import KATA_MAPS

    async with operator_client(store) as (client, partner):
        other = await store.create_partner(
            name="Ex24",
            type="money_exchange",
            referral_url="https://example.com/ex24",
        )
        created = await client.post(
            "/api/places",
            json={
                "name": "Касса",
                "category": "shop",
                "maps_url": KATA_MAPS,
                "partner_id": str(partner.id),
            },
        )
        assert created.status_code == 201
        assert created.json()["maps_url"] == KATA_MAPS
        place_id = created.json()["id"]
        path = f"/api/places/{place_id}/maps"

        first = await client.get(path, follow_redirects=False)
        second = await client.get(path, follow_redirects=False)
        assert first.status_code == 302
        assert first.headers["location"] == KATA_MAPS
        assert second.status_code == 302

        created_user = await client.post(
            "/api/partner-users",
            json={
                "email": "shop@example.com",
                "password": "shop-secret",
                "partner_ids": [str(partner.id), str(other.id)],
            },
        )
        assert created_user.status_code == 201
        login = await client.post(
            "/api/partner/auth/login",
            json={"email": "shop@example.com", "password": "shop-secret"},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        async def opens(partner_id) -> dict:
            stats = await client.get(
                f"/api/partner/stats?partner_id={partner_id}",
                headers=headers,
            )
            assert stats.status_code == 200
            body = stats.json()
            assert body["all_time"]["referral_clicks"] == 0
            return body

        assert (await opens(partner.id))["map_opens"] == 2
        assert (await opens(other.id))["map_opens"] == 0

        moved = await client.patch(
            f"/api/places/{place_id}",
            json={
                "name": "Касса",
                "category": "shop",
                "maps_url": KATA_MAPS,
                "partner_id": str(other.id),
            },
        )
        assert moved.status_code == 200
        third = await client.get(path, follow_redirects=False)
        assert third.status_code == 302
        assert (await opens(partner.id))["map_opens"] == 2
        assert (await opens(other.id))["map_opens"] == 1

        async with store.pool.acquire() as conn:
            await conn.execute("DELETE FROM places WHERE id = $1", place_id)
        missing = await client.get(path, follow_redirects=False)
        assert missing.status_code == 404
        assert (await opens(partner.id))["map_opens"] == 2
        assert (await opens(other.id))["map_opens"] == 1

        plain = await client.post(
            "/api/places",
            json={"name": "Якорная", "category": "beach", "maps_url": KATA_MAPS.replace("Kata", "Shore")},
        )
        assert plain.status_code == 201
        plain_open = await client.get(
            f"/api/places/{plain.json()['id']}/maps",
            follow_redirects=False,
        )
        assert plain_open.status_code == 302
        assert plain_open.headers["location"] == plain.json()["maps_url"]
        assert (await opens(partner.id))["map_opens"] == 2
        assert (await opens(other.id))["map_opens"] == 1
