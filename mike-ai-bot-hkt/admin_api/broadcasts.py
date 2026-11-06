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
    BroadcastList,
    BroadcastListMessage,
    BroadcastListInUse,
    BroadcastLocked,
    add_broadcast_list_message,
    create_broadcast as save_broadcast,
    IntervalBroadcast,
    create_broadcast_list,
    create_interval_broadcast,
    delete_broadcast as remove_broadcast,
    delete_broadcast_list,
    delete_interval_broadcast,
    list_broadcast_lists,
    list_interval_broadcasts,
    list_broadcasts as load_broadcasts,
    move_broadcast_list_message,
    update_broadcast as save_broadcast_update,
    update_interval_broadcast,
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


class BroadcastListIn(BaseModel):
    name: str


class BroadcastListMessageIn(BaseModel):
    text: str
    button_url: Optional[str] = None
    button_label: Optional[str] = None


class BroadcastListMoveIn(BaseModel):
    direction: str


class IntervalBroadcastIn(BaseModel):
    list_id: UUID
    scheduled_at: datetime
    interval_days: int


class IntervalBroadcastUpdate(BaseModel):
    interval_days: Optional[int] = None
    scheduled_at: Optional[datetime] = None


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
    deleted = await remove_broadcast(_store(request).pool, broadcast_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")


def _message_payload(message: BroadcastListMessage) -> dict:
    return {
        "id": str(message.id),
        "text": message.text,
        "button_url": message.button_url,
        "button_label": message.button_label,
    }


def _list_payload(item: BroadcastList) -> dict:
    return {
        "id": str(item.id),
        "name": item.name,
        "messages": [_message_payload(message) for message in item.messages],
    }


@router.post("/api/broadcast-lists", status_code=201)
async def create_list(
    request: Request,
    body: BroadcastListIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    created = await create_broadcast_list(_store(request).pool, name=body.name)
    return _list_payload(created)


@router.get("/api/broadcast-lists")
async def get_lists(
    request: Request,
    admin: AdminUser = Depends(require_admin),
) -> list[dict]:
    _ = admin
    items = await list_broadcast_lists(_store(request).pool)
    return [_list_payload(item) for item in items]


@router.post("/api/broadcast-lists/{list_id}/messages", status_code=201)
async def create_list_message(
    request: Request,
    list_id: UUID,
    body: BroadcastListMessageIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Введите текст сообщения")
    button_url = (body.button_url or "").strip()
    button_label = None
    if button_url:
        resolved = resolve_maps_link(button_url, request.app.state.maps_fetch)
        if resolved is None:
            raise HTTPException(status_code=400, detail="В ссылке нет координат")
        button_url = resolved[0]
        button_label = (body.button_label or "").strip() or ROUTE_BUTTON_LABEL
    else:
        button_url = None
    created = await add_broadcast_list_message(
        _store(request).pool,
        list_id,
        text=text,
        button_url=button_url,
        button_label=button_label,
    )
    if created is None:
        raise HTTPException(status_code=404, detail="Список не найден")
    return _message_payload(created)


@router.post("/api/broadcast-lists/{list_id}/messages/{message_id}/move")
async def move_list_message(
    request: Request,
    list_id: UUID,
    message_id: UUID,
    body: BroadcastListMoveIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    if body.direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Укажите направление")
    moved = await move_broadcast_list_message(
        _store(request).pool,
        list_id,
        message_id,
        direction=body.direction,
    )
    if not moved:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    return {"ok": True}


@router.delete("/api/broadcast-lists/{list_id}", status_code=204)
async def delete_list(
    request: Request,
    list_id: UUID,
    admin: AdminUser = Depends(require_admin),
) -> None:
    _ = admin
    try:
        deleted = await delete_broadcast_list(_store(request).pool, list_id)
    except BroadcastListInUse:
        raise HTTPException(status_code=409, detail="Список используют рассылки") from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Список не найден")


def _interval_payload(item: IntervalBroadcast) -> dict:
    return {
        "id": str(item.id),
        "list_id": str(item.list_id),
        "list_name": item.list_name,
        "interval_days": item.interval_days,
        "scheduled_at": broadcast_scheduled_at(item.scheduled_at),
        "next_message": None if item.next_message is None else _message_payload(item.next_message),
    }


@router.post("/api/interval-broadcasts", status_code=201)
async def create_interval(
    request: Request,
    body: IntervalBroadcastIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    if body.scheduled_at.tzinfo is None or body.scheduled_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Укажите будущее время по Бангкоку")
    if body.interval_days < 1:
        raise HTTPException(status_code=400, detail="Укажите интервал в днях")
    created = await create_interval_broadcast(
        _store(request).pool,
        list_id=body.list_id,
        scheduled_at=body.scheduled_at,
        interval_days=body.interval_days,
    )
    if created is None:
        raise HTTPException(status_code=404, detail="Список не найден")
    return _interval_payload(created)


@router.get("/api/interval-broadcasts")
async def get_intervals(
    request: Request,
    admin: AdminUser = Depends(require_admin),
) -> list[dict]:
    _ = admin
    items = await list_interval_broadcasts(_store(request).pool)
    return [_interval_payload(item) for item in items]


@router.patch("/api/interval-broadcasts/{broadcast_id}")
async def update_interval(
    request: Request,
    broadcast_id: UUID,
    body: IntervalBroadcastUpdate,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    if body.interval_days is not None and body.interval_days < 1:
        raise HTTPException(status_code=400, detail="Укажите интервал в днях")
    if body.scheduled_at is not None and (
        body.scheduled_at.tzinfo is None or body.scheduled_at <= datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="Укажите будущее время по Бангкоку")
    updated = await update_interval_broadcast(
        _store(request).pool,
        broadcast_id,
        interval_days=body.interval_days,
        scheduled_at=body.scheduled_at,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")
    return _interval_payload(updated)


@router.delete("/api/interval-broadcasts/{broadcast_id}", status_code=204)
async def delete_interval(
    request: Request,
    broadcast_id: UUID,
    admin: AdminUser = Depends(require_admin),
) -> None:
    _ = admin
    deleted = await delete_interval_broadcast(_store(request).pool, broadcast_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Рассылка не найдена")
