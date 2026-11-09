"""Public map payload for the mini app."""

from __future__ import annotations

from fastapi import APIRouter, Request

from tma_map import list_map_pins, maps_browser_key

router = APIRouter()


@router.get("/api/map")
async def map_view(request: Request) -> dict:
    pins = await list_map_pins(request.app.state.store, request.app.state.storage)
    return {"key": maps_browser_key(), "pins": pins}
