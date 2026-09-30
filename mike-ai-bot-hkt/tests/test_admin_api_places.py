from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import S3_BUCKET, S3_ENV, requires_db

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64

PROMTEP_MAPS = (
    "https://www.google.com/maps/place/Promthep+Cape/"
    "@7.7600,98.3000,17z/data=!4m6!3m5!1s0x0!8m2!3d7.7622!4d98.3055"
)
KATA_MAPS = (
    "https://www.google.com/maps/place/Kata/"
    "@7.8200,98.3000,17z/data=!4m6!3m5!1s0x0!8m2!3d7.8201!4d98.2980"
)


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


@asynccontextmanager
async def authed_client(store, storage=None, maps_fetch=None):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    kwargs = {}
    if storage is not None:
        kwargs["storage"] = storage
    if maps_fetch is not None:
        kwargs["maps_fetch"] = maps_fetch
    app = create_app(store=store, **kwargs)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        yield client


@requires_db
@pytest.mark.asyncio
async def test_create_place_from_maps_url_appears_in_admin_list(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
            },
        )
        assert created.status_code == 201
        body = created.json()
        assert body["name"] == "Мыс Промтеп"
        assert body["category"] == "beach"
        assert body["maps_url"] == PROMTEP_MAPS
        assert body["latitude"] == pytest.approx(7.7622)
        assert body["longitude"] == pytest.approx(98.3055)

        listed = await client.get("/api/places")
        assert listed.status_code == 200
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["category"] == "beach"
        assert match["latitude"] == pytest.approx(7.7622)
        assert match["longitude"] == pytest.approx(98.3055)
        assert match["maps_url"] == PROMTEP_MAPS


@requires_db
@pytest.mark.asyncio
async def test_create_place_rejects_maps_url_without_a_pin(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/places",
            json={
                "name": "Без пина",
                "category": "beach",
                "maps_url": "https://www.google.com/maps/search/?api=1&query=Phuket",
            },
        )
        assert created.status_code == 400

        listed = await client.get("/api/places")
        names = {item["name"] for item in listed.json()}
        assert "Без пина" not in names


@requires_db
@pytest.mark.asyncio
async def test_create_place_rejects_duplicate_maps_url(store):
    async with authed_client(store) as client:
        first = await client.post(
            "/api/places",
            json={"name": "Мыс Промтеп", "category": "beach", "maps_url": PROMTEP_MAPS},
        )
        assert first.status_code == 201

        second = await client.post(
            "/api/places",
            json={"name": "Мыс Промтеп ещё раз", "category": "beach", "maps_url": PROMTEP_MAPS},
        )
        assert second.status_code == 409

        listed = await client.get("/api/places")
        names = {item["name"] for item in listed.json()}
        assert names == {"Мыс Промтеп"}


@requires_db
@pytest.mark.asyncio
async def test_inactive_partner_hides_place_from_tourists_and_keeps_it_in_admin(store):
    async with authed_client(store) as client:
        partner = await client.post(
            "/api/partners",
            json={
                "name": "Money Shop",
                "type": "money_exchange",
                "referral_url": "https://example.com/money",
                "is_active": False,
            },
        )
        assert partner.status_code == 201

        unlinked = await client.post(
            "/api/places",
            json={"name": "Мыс Промтеп", "category": "beach", "maps_url": PROMTEP_MAPS},
        )
        assert unlinked.status_code == 201
        assert unlinked.json()["partner_id"] is None

        linked = await client.post(
            "/api/places",
            json={
                "name": "Касса Ката",
                "category": "shop",
                "maps_url": KATA_MAPS,
                "partner_id": partner.json()["id"],
            },
        )
        assert linked.status_code == 201
        assert linked.json()["partner_id"] == partner.json()["id"]

        listed = await client.get("/api/places")
        names = {item["name"] for item in listed.json()}
        assert names == {"Мыс Промтеп", "Касса Ката"}

    visible = {place.name for place in await store.list_visible_places()}
    assert visible == {"Мыс Промтеп"}


@requires_db
@pytest.mark.asyncio
async def test_create_place_without_photos_uses_placeholder_cover(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/places",
            json={"name": "Мыс Промтеп", "category": "beach", "maps_url": PROMTEP_MAPS},
        )
        assert created.status_code == 201
        assert created.json()["photos"] == []
        assert created.json()["cover"] == "media/places/placeholder.jpg"

        listed = await client.get("/api/places")
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["cover"] == "media/places/placeholder.jpg"


@requires_db
@pytest.mark.asyncio
async def test_chosen_photo_is_stored_as_the_cover(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        png = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("front.png", PNG, "image/png")},
        )
        jpeg = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("cover.jpg", JPEG, "image/jpeg")},
        )
        assert png.status_code == 201
        assert jpeg.status_code == 201

        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [
                    {"upload_token": png.json()["upload_token"], "is_cover": False},
                    {"upload_token": jpeg.json()["upload_token"], "is_cover": True},
                ],
            },
        )
        assert created.status_code == 201
        photos = created.json()["photos"]
        assert [photo["path"].rsplit(".", 1)[-1] for photo in photos] == ["jpg", "png"]
        assert created.json()["cover"] == photos[0]["path"]

        listed = await client.get("/api/places")
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["cover"] == photos[0]["path"]
        assert [photo["path"] for photo in match["photos"]] == [photo["path"] for photo in photos]


@requires_db
@pytest.mark.asyncio
async def test_saved_place_photo_has_a_public_url(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        uploaded = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("front.jpg", JPEG, "image/jpeg")},
        )
        assert uploaded.status_code == 201

        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [{"upload_token": uploaded.json()["upload_token"]}],
            },
        )
        assert created.status_code == 201
        photo = created.json()["photos"][0]
        assert photo["url"] == f"{S3_ENV['S3_PUBLIC_BASE_URL']}/{photo['path']}"

        listed = await client.get("/api/places")
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["photos"][0]["url"] == photo["url"]


@requires_db
@pytest.mark.asyncio
async def test_text_update_keeps_the_place_photo(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        uploaded = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("front.jpg", JPEG, "image/jpeg")},
        )
        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [{"upload_token": uploaded.json()["upload_token"]}],
            },
        )
        assert created.status_code == 201
        photo_url = created.json()["photos"][0]["url"]

        updated = await client.patch(
            f"/api/places/{created.json()['id']}",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "blurb": "Закат",
            },
        )
        assert updated.status_code == 200
        assert updated.json()["blurb"] == "Закат"
        assert updated.json()["photos"][0]["url"] == photo_url


def _bucket_keys(s3) -> list[str]:
    return sorted(item["Key"] for item in s3.list_objects_v2(Bucket=S3_BUCKET).get("Contents", []))


@requires_db
@pytest.mark.asyncio
async def test_photo_update_replaces_every_stored_photo(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        png = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("front.png", PNG, "image/png")},
        )
        jpeg = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("cover.jpg", JPEG, "image/jpeg")},
        )
        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [
                    {"upload_token": png.json()["upload_token"], "is_cover": False},
                    {"upload_token": jpeg.json()["upload_token"], "is_cover": True},
                ],
            },
        )
        assert created.status_code == 201
        assert len(created.json()["photos"]) == 2

        replacement = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("new.jpg", JPEG, "image/jpeg")},
        )
        updated = await client.patch(
            f"/api/places/{created.json()['id']}",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [{"upload_token": replacement.json()["upload_token"]}],
            },
        )
        assert updated.status_code == 200
        photos = updated.json()["photos"]
        assert len(photos) == 1
        assert photos[0]["url"] == f"{S3_ENV['S3_PUBLIC_BASE_URL']}/{photos[0]['path']}"
        assert _bucket_keys(s3) == [photos[0]["path"]]


@requires_db
@pytest.mark.asyncio
async def test_empty_photo_list_removes_the_place_photo(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        uploaded = await client.post(
            "/api/place-photos/uploads",
            files={"file": ("front.jpg", JPEG, "image/jpeg")},
        )
        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [{"upload_token": uploaded.json()["upload_token"]}],
            },
        )
        assert created.status_code == 201
        assert created.json()["photos"]

        updated = await client.patch(
            f"/api/places/{created.json()['id']}",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "photos": [],
            },
        )
        assert updated.status_code == 200
        assert updated.json()["photos"] == []
        assert _bucket_keys(s3) == []

        listed = await client.get("/api/places")
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["photos"] == []


@requires_db
@pytest.mark.asyncio
async def test_deactivating_a_place_hides_it_from_tourists(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/places",
            json={"name": "Мыс Промтеп", "category": "beach", "maps_url": PROMTEP_MAPS},
        )
        assert created.status_code == 201

        updated = await client.patch(
            f"/api/places/{created.json()['id']}",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "is_active": False,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["is_active"] is False

        listed = await client.get("/api/places")
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["is_active"] is False

    visible = {place.name for place in await store.list_visible_places()}
    assert "Мыс Промтеп" not in visible


@requires_db
@pytest.mark.asyncio
async def test_short_maps_link_is_stored_as_the_long_url(store):
    def follow(url: str) -> str:
        assert url == "https://maps.app.goo.gl/promthep"
        return PROMTEP_MAPS

    async with authed_client(store, maps_fetch=follow) as client:
        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": "https://maps.app.goo.gl/promthep",
            },
        )
        assert created.status_code == 201
        assert created.json()["maps_url"] == PROMTEP_MAPS
        assert created.json()["latitude"] == pytest.approx(7.7622)
        assert created.json()["longitude"] == pytest.approx(98.3055)


@requires_db
@pytest.mark.asyncio
async def test_create_place_stores_optional_blurb(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/places",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "blurb": "Закат",
            },
        )
        assert created.status_code == 201
        assert created.json()["blurb"] == "Закат"

        listed = await client.get("/api/places")
        match = next(item for item in listed.json() if item["name"] == "Мыс Промтеп")
        assert match["blurb"] == "Закат"


@requires_db
@pytest.mark.asyncio
async def test_place_is_not_recommended_until_admin_sets_yes(store):
    async with authed_client(store) as client:
        created = await client.post(
            "/api/places",
            json={"name": "Мыс Промтеп", "category": "beach", "maps_url": PROMTEP_MAPS},
        )
        assert created.status_code == 201
        assert created.json()["mike_recommends"] is False

        catalog = await client.get("/api/catalog/places")
        assert catalog.status_code == 200
        match = next(item for item in catalog.json() if item["name"] == "Мыс Промтеп")
        assert match["mike_recommends"] is False

        updated = await client.patch(
            f"/api/places/{created.json()['id']}",
            json={
                "name": "Мыс Промтеп",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "mike_recommends": True,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["mike_recommends"] is True

        catalog = await client.get("/api/catalog/places")
        match = next(item for item in catalog.json() if item["name"] == "Мыс Промтеп")
        assert match["mike_recommends"] is True


@requires_db
@pytest.mark.asyncio
async def test_public_catalog_is_open_and_lists_visible_places(store, asset_storage):
    async with authed_client(store, asset_storage) as client:
        partner = await client.post(
            "/api/partners",
            json={
                "name": "Money Shop",
                "type": "money_exchange",
                "referral_url": "https://example.com/money",
                "is_active": False,
            },
        )
        assert partner.status_code == 201

        recommended = await client.post(
            "/api/places",
            json={
                "name": "Якорная",
                "category": "beach",
                "maps_url": PROMTEP_MAPS,
                "blurb": "Закат",
                "mike_recommends": True,
            },
        )
        assert recommended.status_code == 201

        plain = await client.post(
            "/api/places",
            json={
                "name": "Анапа",
                "category": "shop",
                "maps_url": KATA_MAPS,
            },
        )
        assert plain.status_code == 201

        inactive = await client.post(
            "/api/places",
            json={
                "name": "Скрытый",
                "category": "beach",
                "maps_url": PROMTEP_MAPS.replace("Promthep+Cape", "Hidden"),
                "is_active": False,
            },
        )
        assert inactive.status_code == 201

        closed = await client.post(
            "/api/places",
            json={
                "name": "Касса",
                "category": "shop",
                "maps_url": KATA_MAPS.replace("Kata", "Kassa"),
                "partner_id": partner.json()["id"],
            },
        )
        assert closed.status_code == 201

    from admin_api.app import create_app

    app = create_app(store=store, storage=asset_storage)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as public:
        catalog = await public.get("/api/catalog/places")

    assert catalog.status_code == 200
    places = catalog.json()
    assert [place["name"] for place in places] == ["Якорная", "Анапа"]
    assert places[0]["mike_recommends"] is True
    assert places[0]["category"] == "Пляж"
    assert places[0]["blurb"] == "Закат"
    assert places[0]["maps_url"] == PROMTEP_MAPS
    assert places[0]["photo_url"] == (
        "https://cdn-test.mikephuketai.com/media/places/placeholder.jpg"
    )
    assert places[1]["mike_recommends"] is False
    assert places[1]["category"] == "Магазин"
    assert all("partner_id" not in place for place in places)
