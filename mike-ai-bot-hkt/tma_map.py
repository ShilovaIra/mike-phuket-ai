"""Pins for the mini-app map.

Visible places only. A place without coordinates is left off the map.
The browser key is separate from the server Places key.
"""

from __future__ import annotations

import math
import os
from typing import Any

from place_catalog import Place
from place_maps import tracked_maps_url

PLACEHOLDER_COVER = "media/places/placeholder.jpg"
MAPS_JS_KEY = "GOOGLE_MAPS_JS_API_KEY"


def maps_browser_key(environ: Any | None = None) -> str:
    source = os.environ if environ is None else environ
    return (source.get(MAPS_JS_KEY) or "").strip()


def has_coordinates(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return False
    return math.isfinite(lat) and math.isfinite(lng)


def map_pin(place: Place, category: str, photo_url: str, category_slug: str = "") -> dict:
    return {
        "id": str(place.id),
        "name": place.name,
        "category": category,
        "category_slug": category_slug,
        "blurb": place.blurb or "",
        "maps_url": tracked_maps_url(
            place_id=place.id, partner_id=place.partner_id, maps_url=place.maps_url
        ),
        "photo_url": photo_url,
        "mike_recommends": place.mike_recommends,
        "latitude": float(place.latitude),
        "longitude": float(place.longitude),
    }


async def list_map_pins(store: Any, storage: Any | None) -> list[dict]:
    categories = {item.id: item for item in await store.list_place_categories()}
    pins = []
    for place in await store.list_visible_places():
        if not has_coordinates(place.latitude, place.longitude):
            continue
        assets = await store.list_place_assets(place.id)
        cover = assets[0].path if assets else PLACEHOLDER_COVER
        photo_url = storage.public_url(cover) if storage is not None else cover
        category = categories.get(place.category_id)
        pins.append(
            map_pin(
                place,
                category.label if category else "",
                photo_url,
                category.slug if category else "",
            )
        )
    return pins
