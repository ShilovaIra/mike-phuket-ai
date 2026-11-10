from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from place_catalog import Place, PlaceAsset, PlaceCategory
from tests.conftest import requires_db
from tests.test_admin_api_places import KATA_MAPS, PROMTEP_MAPS, authed_client
from tma_map import has_coordinates, list_map_pins, map_pin, maps_browser_key


def _place(**overrides) -> Place:
    fields = dict(
        id=uuid4(),
        name="Якорная",
        category_id=uuid4(),
        partner_id=None,
        google_place_id=None,
        latitude=7.7622,
        longitude=98.3055,
        blurb="Закат",
        is_active=True,
        maps_url="https://maps.example/promthep",
        mike_recommends=True,
    )
    fields.update(overrides)
    return Place(**fields)


def test_map_route_is_mounted():
    from admin_api.app import create_app

    app = create_app(store=object(), storage=None)
    paths = {route.path for route in app.routes}
    assert "/api/map" in paths
    assert "/api/places/{place_id}/maps" in paths


def test_browser_key_is_the_maps_js_key_only(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_JS_API_KEY", " browser-key ")
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "server-key")
    assert maps_browser_key() == "browser-key"


def test_a_place_without_coordinates_is_not_a_pin():
    assert has_coordinates(7.76, 98.30)
    assert not has_coordinates(None, 98.30)
    assert not has_coordinates(float("nan"), 98.30)


def test_a_linked_place_pin_counts_through_our_redirect():
    place = _place(partner_id=uuid4())
    pin = map_pin(place, "Магазин", "https://cdn.example/office.jpg")
    assert pin["maps_url"] == f"/api/places/{place.id}/maps"


def test_pin_carries_the_place_card_and_its_point():
    place = _place()
    pin = map_pin(place, "Пляж", "https://cdn.example/promthep.jpg")
    assert pin == {
        "id": str(place.id),
        "name": "Якорная",
        "category": "Пляж",
        "category_slug": "",
        "blurb": "Закат",
        "maps_url": "https://maps.example/promthep",
        "photo_url": "https://cdn.example/promthep.jpg",
        "mike_recommends": True,
        "latitude": pytest.approx(7.7622),
        "longitude": pytest.approx(98.3055),
    }


class _Storage:
    def public_url(self, path: str) -> str:
        return f"https://cdn.example/{path}"


class _Store:
    def __init__(self, places, categories, assets):
        self._places = places
        self._categories = categories
        self._assets = assets

    async def list_visible_places(self):
        return self._places

    async def list_place_categories(self):
        return self._categories

    async def list_place_assets(self, place_id):
        return self._assets.get(place_id, [])


@pytest.mark.asyncio
async def test_listed_pins_skip_a_place_with_no_point_and_use_its_cover():
    beach = uuid4()
    shop = uuid4()
    kept = _place(category_id=beach)
    dropped = _place(name="Пусто", category_id=shop, latitude=None, longitude=None)
    cover = PlaceAsset(id=uuid4(), place_id=kept.id, path="places/yakornaya.jpg", sort_order=0)
    store = _Store(
        [kept, dropped],
        [
            PlaceCategory(id=beach, slug="beach", label="Пляж", sort_order=1),
            PlaceCategory(id=shop, slug="shop", label="Магазин", sort_order=2),
        ],
        {kept.id: [cover]},
    )

    pins = await list_map_pins(store, _Storage())

    assert [pin["name"] for pin in pins] == ["Якорная"]
    assert pins[0]["category"] == "Пляж"
    assert pins[0]["photo_url"] == "https://cdn.example/places/yakornaya.jpg"


@pytest.mark.asyncio
async def test_a_listed_pin_carries_its_category_slug():
    beach = uuid4()
    place = _place(category_id=beach)
    store = _Store(
        [place],
        [PlaceCategory(id=beach, slug="beach", label="Пляж", sort_order=1)],
        {},
    )

    pins = await list_map_pins(store, _Storage())

    assert pins[0]["category"] == "Пляж"
    assert pins[0]["category_slug"] == "beach"


@requires_db
@pytest.mark.asyncio
async def test_public_map_lists_visible_places_and_the_browser_key(store, asset_storage, monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_JS_API_KEY", "browser-key")
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
            json={"name": "Анапа", "category": "shop", "maps_url": KATA_MAPS},
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
        body = (await public.get("/api/map")).json()

    assert body["key"] == "browser-key"
    pins = {pin["name"]: pin for pin in body["pins"]}
    assert set(pins) == {"Якорная", "Анапа"}
    assert pins["Якорная"]["mike_recommends"] is True
    assert pins["Якорная"]["category"] == "Пляж"
    assert pins["Якорная"]["category_slug"] == "beach"
    assert pins["Анапа"]["category_slug"] == "shop"
    assert pins["Якорная"]["latitude"] == pytest.approx(7.7622)
    assert pins["Якорная"]["longitude"] == pytest.approx(98.3055)
    assert pins["Анапа"]["mike_recommends"] is False
    assert pins["Анапа"]["latitude"] == pytest.approx(7.8201)
