from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from admin_api.deps import require_admin
from broadcasts import (
    Broadcast,
    BroadcastLocked,
    create_broadcast as save_broadcast,
    delete_broadcast as remove_broadcast,
    list_broadcasts as load_broadcasts,
    update_broadcast as save_broadcast_update,
)
from db.store import AdminUser, SessionStore
from maps_pin import resolve_maps_link

router = APIRouter()

ROUTE_BUTTON_LABEL = "Проложить маршрут"
BANGKOK = ZoneInfo("Asia/Bangkok")


def broadcast_scheduled_at(value: datetime) -> str:
    return value.astimezone(BANGKOK).isoformat(timespec="seconds")


class BroadcastIn(BaseModel):
    text: str
    scheduled_at: datetime
    button_url: Optional[str] = None
    button_label: Optional[str] = None


def _store(request: Request) -> SessionStore:
    return request.app.state.store


def _broadcast_payload(broadcast: Broadcast) -> dict:
    return {
        "id": str(broadcast.id),
        "text": broadcast.text,
        "scheduled_at": broadcast_scheduled_at(broadcast.scheduled_at),
        "status": broadcast.status,
        "button_url": broadcast.button_url,
        "button_label": broadcast.button_label,
    }


def _broadcast_write(
    body: BroadcastIn, maps_fetch
) -> tuple[str, datetime, Optional[str], Optional[str]]:
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Введите текст сообщения")
    if body.scheduled_at.tzinfo is None or body.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Укажите будущее время по Бангкоку")
    button_url = (body.button_url or "").strip()
    if not button_url:
        return text, body.scheduled_at, None, None
    resolved = resolve_maps_link(button_url, maps_fetch)
    if resolved is None:
        raise HTTPException(status_code=400, detail="В ссылке нет координат")
    label = (body.button_label or "").strip() or ROUTE_BUTTON_LABEL
    return text, body.scheduled_at, resolved[0], label


@router.get("/api/broadcasts")
async def list_broadcasts(
    request: Request,
    admin: AdminUser = Depends(require_admin),
) -> list[dict]:
    _ = admin
    items = await load_broadcasts(_store(request).pool)
    return [_broadcast_payload(item) for item in items]


@router.post("/api/broadcasts", status_code=201)
async def create_broadcast(
    request: Request,
    body: BroadcastIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    text, scheduled_at, button_url, button_label = _broadcast_write(
        body, request.app.state.maps_fetch
    )
    created = await save_broadcast(
        _store(request).pool,
        text=text,
        scheduled_at=scheduled_at,
        button_url=button_url,
        button_label=button_label,
    )
    return _broadcast_payload(created)


@router.patch("/api/broadcasts/{broadcast_id}")
async def update_broadcast(
    request: Request,
    broadcast_id: UUID,
    body: BroadcastIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    text, scheduled_at, button_url, button_label = _broadcast_write(
        body, request.app.state.maps_fetch
    )
    try:
        updated = await save_broadcast_update(
            _store(request).pool,
            broadcast_id,
            text=text,
            scheduled_at=scheduled_at,
            button_url=button_url,
            button_label=button_label,
        )
    except BroadcastLocked:
        raise HTTPException(status_code=409, detail="Рассылка уже отправляется") from None
    if updated is None:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")
    return _broadcast_payload(updated)


@router.delete("/api/broadcasts/{broadcast_id}", status_code=204)
async def delete_broadcast(
    request: Request,
    broadcast_id: UUID,
    admin: AdminUser = Depends(require_admin),
) -> None:
    _ = admin
    try:
        deleted = await remove_broadcast(_store(request).pool, broadcast_id)
    except BroadcastLocked:
        raise HTTPException(status_code=409, detail="Рассылка уже отправляется") from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")
