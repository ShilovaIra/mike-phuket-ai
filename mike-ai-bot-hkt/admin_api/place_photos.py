from __future__ import annotations

import logging
from pathlib import PurePosixPath
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from admin_api.deps import require_admin
from admin_api.tokens import create_logo_upload_token, decode_logo_upload_token
from db.store import AdminUser, SessionStore
from place_catalog import PlaceAsset
from storage import AssetStorage, StorageError

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_PHOTO_BYTES = 5 * 1024 * 1024
STORAGE_DOWN = "Хранилище недоступно, попробуйте позже"
UPLOAD_EXPIRED = "Загрузка устарела, выберите файл заново"

_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
)


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


@router.post("/api/place-photos/uploads", status_code=201)
async def upload_place_photo(
    request: Request,
    file: UploadFile = File(...),
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    data = await file.read(MAX_PHOTO_BYTES + 1)
    if len(data) > MAX_PHOTO_BYTES:
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
        logger.exception("Place photo upload to storage failed")
        raise HTTPException(status_code=503, detail=STORAGE_DOWN) from None
    return {"upload_token": create_logo_upload_token(key=key), "preview_url": preview_url}


async def attach_place_photos(request: Request, place_id: UUID, photos: list) -> list[PlaceAsset]:
    if not photos:
        return []
    storage = _require_storage(request)
    store = _store(request)
    cover = next((photo for photo in photos if photo.is_cover), photos[0])
    ordered = [cover, *[photo for photo in photos if photo is not cover]]
    for sort_order, photo in enumerate(ordered):
        try:
            staged_key = decode_logo_upload_token(photo.upload_token)
        except jwt.PyJWTError:
            raise HTTPException(status_code=400, detail=UPLOAD_EXPIRED) from None
        staged = PurePosixPath(staged_key)
        key = f"places/{place_id}/{staged.stem[:12]}{staged.suffix}"
        try:
            await run_in_threadpool(storage.copy, staged_key, key)
        except StorageError:
            logger.exception("Linking staged place photo %s failed", staged_key)
            raise HTTPException(status_code=503, detail=STORAGE_DOWN) from None
        await store.add_place_asset(place_id, key, sort_order)
        try:
            await run_in_threadpool(storage.delete, staged_key)
        except StorageError:
            logger.warning("Could not delete %s from storage", staged_key, exc_info=True)
    return await store.list_place_assets(place_id)
