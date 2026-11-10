"""Public map payload for the mini app."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from place_maps import open_place_maps
from tma_map import list_map_pins, maps_browser_key

router = APIRouter()


@router.get("/api/map")
async def map_view(request: Request) -> dict:
    pins = await list_map_pins(request.app.state.store, request.app.state.storage)
    return {"key": maps_browser_key(), "pins": pins}


@router.get("/api/places/{place_id}/maps")
async def open_place_in_maps(request: Request, place_id: UUID) -> RedirectResponse:
    url = await open_place_maps(request.app.state.store.pool, place_id)
    if url is None:
        raise HTTPException(status_code=404, detail="Not found")
    return RedirectResponse(url=url, status_code=302)
