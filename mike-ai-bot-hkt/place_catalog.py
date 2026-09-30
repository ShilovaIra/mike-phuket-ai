from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PlaceCategory:
    id: UUID
    slug: str
    label: str
    sort_order: int


@dataclass(frozen=True)
class Place:
    id: UUID
    name: str
    category_id: UUID
    partner_id: UUID | None
    google_place_id: str | None
    latitude: float
    longitude: float
    blurb: str | None
    is_active: bool
    maps_url: str | None = None
    mike_recommends: bool = False


@dataclass(frozen=True)
class PlaceAsset:
    id: UUID
    place_id: UUID
    path: str
    sort_order: int
