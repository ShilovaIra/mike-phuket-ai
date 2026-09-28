from __future__ import annotations

import logging
from pathlib import PurePosixPath
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from admin_api.deps import require_admin
from admin_api.payloads import partner_payload
from admin_api.tokens import create_logo_upload_token, decode_logo_upload_token
from db.store import AdminUser, SessionStore
from partners import is_bundled_logo
from storage import AssetStorage, StorageError

logger = logging.getLogger(__name__)

router = APIRouter()

STORAGE_DOWN = "Хранилище недоступно, попробуйте позже"
UPLOAD_EXPIRED = "Загрузка устарела, выберите файл заново"
PARTNER_NOT_FOUND = "Партнёр не найден"

# Telegram fetches photos by URL only up to 5 MB.
MAX_LOGO_BYTES = 5 * 1024 * 1024

_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
)


class LinkLogoIn(BaseModel):
    upload_token: str


def _sniff(data: bytes) -> tuple[str, str] | None:
    for signature, extension, content_type in _SIGNATURES:
        if data.startswith(signature):
            return extension, content_type
    return None


def _require_storage(request: Request) -> AssetStorage:
    storage: AssetStorage | None = request.app.state.storage
    if storage is None:
        raise HTTPException(status_code=503, detail=STORAGE_DOWN)
    return storage


def _store(request: Request) -> SessionStore:
    return request.app.state.store


async def _delete_quietly(storage: AssetStorage, key: str) -> None:
    try:
        await run_in_threadpool(storage.delete, key)
    except StorageError:
        logger.warning("Could not delete %s from storage", key, exc_info=True)


@router.post("/api/partner-logos/uploads", status_code=201)
async def upload_partner_logo(
    request: Request,
    file: UploadFile = File(...),
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    data = await file.read(MAX_LOGO_BYTES + 1)
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Файл больше 5 МБ")
    sniffed = _sniff(data)
    if sniffed is None:
        raise HTTPException(status_code=400, detail="Только JPEG или PNG")
    extension, content_type = sniffed
    storage = _require_storage(request)
    key = f"tmp/{uuid4().hex}.{extension}"
    try:
        preview_url = await run_in_threadpool(storage.upload, key, data, content_type)
    except StorageError:
        logger.exception("Logo upload to storage failed")
        raise HTTPException(status_code=503, detail=STORAGE_DOWN) from None
    return {"upload_token": create_logo_upload_token(key=key), "preview_url": preview_url}


@router.put("/api/partners/{partner_id}/logo")
async def link_partner_logo(
    request: Request,
    partner_id: UUID,
    body: LinkLogoIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    storage = _require_storage(request)
    try:
        staged_key = decode_logo_upload_token(body.upload_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail=UPLOAD_EXPIRED) from None

    staged = PurePosixPath(staged_key)
    key = f"partners/{partner_id}/logo-{staged.stem[:12]}{staged.suffix}"
    try:
        await run_in_threadpool(storage.copy, staged_key, key)
    except StorageError:
        logger.exception("Linking staged logo %s failed", staged_key)
        raise HTTPException(status_code=503, detail=STORAGE_DOWN) from None

    try:
        previous, partner = await _store(request).set_partner_logo(partner_id, key)
    except KeyError:
        await _delete_quietly(storage, key)
        raise HTTPException(status_code=404, detail=PARTNER_NOT_FOUND) from None

    await _delete_quietly(storage, staged_key)
    await _delete_previous_upload(storage, previous, keep=key)
    return partner_payload(partner, storage)


@router.delete("/api/partners/{partner_id}/logo")
async def remove_partner_logo(
    request: Request,
    partner_id: UUID,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    try:
        previous, partner = await _store(request).set_partner_logo(partner_id, None)
    except KeyError:
        raise HTTPException(status_code=404, detail=PARTNER_NOT_FOUND) from None

    storage: AssetStorage | None = request.app.state.storage
    if storage is not None:
        await _delete_previous_upload(storage, previous)
    return partner_payload(partner, storage)


async def _delete_previous_upload(
    storage: AssetStorage, previous: str | None, *, keep: str | None = None
) -> None:
    if previous and previous != keep and not is_bundled_logo(previous):
        await _delete_quietly(storage, previous)
