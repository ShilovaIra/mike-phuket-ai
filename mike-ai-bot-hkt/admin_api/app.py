from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from admin_api.deps import require_admin
from admin_api.partner_logos import router as partner_logos_router
from admin_api.place_photos import attach_place_photos
from admin_api.place_photos import router as place_photos_router
from admin_api.passwords import verify_password
from admin_api.payloads import partner_payload
from admin_api.tokens import create_access_token
from db.store import AdminUser, SessionStore
from db.url import resolve_database_url
from partner_dashboard.router import router as partner_dashboard_router
from maps_pin import follow_maps_redirect, resolve_maps_link
from partners import PartnerType
from place_catalog import Place, PlaceAsset, PlaceCategory

PLACEHOLDER_COVER = "media/places/placeholder.jpg"
from storage import AssetStorage
from topic_labels import labeled_topic_rows


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PartnerTypeIn(BaseModel):
    slug: str
    is_menu_visible: bool
    sort_order: int
    button_label: str
    topic_label: str
    intro: str
    fallback: str
    caption_emoji: str
    caption_cta: str
    button_template: str
    follow_up_text: str = ""


class PlaceCategoryIn(BaseModel):
    slug: str
    label: str
    sort_order: int


class PlaceCategoryUpdate(BaseModel):
    label: str
    sort_order: int


class PlacePhotoIn(BaseModel):
    upload_token: str
    is_cover: bool = False


class PlaceIn(BaseModel):
    name: str
    category: str
    maps_url: str
    blurb: str = ""
    partner_id: Optional[UUID] = None
    is_active: bool = True
    photos: List[PlacePhotoIn] = []


class PartnerIn(BaseModel):
    name: str
    type: str
    referral_url: str
    blurb: str = ""
    is_active: bool = True
    sort_order: int = 0


def _partner_type_payload(partner_type: PartnerType) -> dict:
    return asdict(partner_type)


def _place_category_payload(category: PlaceCategory) -> dict:
    payload = asdict(category)
    payload["id"] = str(category.id)
    return payload


def _place_payload(
    place: Place, category_slug: str, assets: list[PlaceAsset] | None = None
) -> dict:
    photos = [{"id": str(asset.id), "path": asset.path} for asset in assets or ()]
    return {
        "id": str(place.id),
        "name": place.name,
        "category": category_slug,
        "maps_url": place.maps_url or "",
        "blurb": place.blurb or "",
        "latitude": place.latitude,
        "longitude": place.longitude,
        "partner_id": None if place.partner_id is None else str(place.partner_id),
        "is_active": place.is_active,
        "photos": photos,
        "cover": photos[0]["path"] if photos else PLACEHOLDER_COVER,
    }


_FROM_ENV = object()


def create_app(
    *,
    store: SessionStore | None = None,
    storage: AssetStorage | None | object = _FROM_ENV,
    maps_fetch=None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        owned = False
        if store is not None:
            app.state.store = store
        else:
            database_url = resolve_database_url()
            if not database_url:
                raise RuntimeError("DATABASE_URL or POSTGRES_* is required")
            app.state.store = await SessionStore.create(database_url)
            owned = True
        yield
        if owned:
            await app.state.store.close()

    app = FastAPI(title="Mike AI Admin API", lifespan=lifespan)
    if store is not None:
        app.state.store = store
    app.state.storage = AssetStorage.from_env(os.environ) if storage is _FROM_ENV else storage
    app.state.maps_fetch = maps_fetch or follow_maps_redirect

    origins = [
        origin.strip()
        for origin in os.environ.get("ADMIN_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _store(request: Request) -> SessionStore:
        return request.app.state.store

    @app.post("/api/auth/login", response_model=LoginResponse)
    async def login(request: Request, body: LoginRequest) -> LoginResponse:
        admin = await _store(request).get_admin_by_email(body.email)
        if admin is None or not verify_password(body.password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        token = create_access_token(admin_id=admin.id, email=admin.email)
        return LoginResponse(access_token=token)

    @app.get("/api/auth/me")
    async def me(admin: AdminUser = Depends(require_admin)) -> dict:
        return {"email": admin.email}

    @app.get("/api/stats")
    async def stats(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        store = _store(request)
        bot_stats = await store.get_bot_stats()
        partner_types = await store.list_partner_types()
        payload = asdict(bot_stats)
        payload["topics_all_time"] = labeled_topic_rows(
            bot_stats.topics_all_time, partner_types
        )
        payload["topics_7d"] = labeled_topic_rows(bot_stats.topics_7d, partner_types)
        return payload

    @app.get("/api/partner-types")
    @app.get("/api/partner-types/", include_in_schema=False)
    async def list_partner_types(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        try:
            items = await _store(request).list_partner_types()
            return [_partner_type_payload(item) for item in items]
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/partner-types", status_code=201)
    async def create_partner_type(
        request: Request,
        body: PartnerTypeIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        try:
            created = await _store(request).create_partner_type(PartnerType(**body.model_dump()))
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Тип с таким slug уже существует") from None
        return _partner_type_payload(created)

    @app.patch("/api/partner-types/{slug}")
    async def update_partner_type(
        request: Request,
        slug: str,
        body: PartnerTypeIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        try:
            updated = await _store(request).update_partner_type(slug, PartnerType(**body.model_dump()))
        except KeyError:
            raise HTTPException(status_code=404, detail="Тип партнёра не найден") from None
        except ValueError:
            raise HTTPException(status_code=409, detail="Тип с таким slug уже существует") from None
        return _partner_type_payload(updated)

    @app.get("/api/place-categories")
    async def list_place_categories(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        items = await _store(request).list_place_categories()
        return [_place_category_payload(item) for item in items]

    @app.post("/api/place-categories", status_code=201)
    async def create_place_category(
        request: Request,
        body: PlaceCategoryIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        created = await _store(request).create_place_category(
            slug=body.slug,
            label=body.label,
            sort_order=body.sort_order,
        )
        return _place_category_payload(created)

    @app.patch("/api/place-categories/{slug}")
    async def update_place_category(
        request: Request,
        slug: str,
        body: PlaceCategoryUpdate,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        updated = await _store(request).update_place_category(
            slug,
            label=body.label,
            sort_order=body.sort_order,
        )
        return _place_category_payload(updated)

    @app.delete("/api/place-categories/{slug}", status_code=204)
    async def delete_place_category(
        request: Request,
        slug: str,
        admin: AdminUser = Depends(require_admin),
    ) -> None:
        _ = admin
        try:
            await _store(request).delete_place_category(slug)
        except asyncpg.ForeignKeyViolationError:
            raise HTTPException(
                status_code=409, detail="Категорию используют места"
            ) from None

    @app.get("/api/places")
    async def list_places(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        store = _store(request)
        categories = {item.id: item.slug for item in await store.list_place_categories()}
        payloads = []
        for place in await store.list_places():
            assets = await store.list_place_assets(place.id)
            payloads.append(
                _place_payload(place, categories[place.category_id], assets)
            )
        return payloads

    @app.post("/api/places", status_code=201)
    async def create_place(
        request: Request,
        body: PlaceIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        store = _store(request)
        category = next(
            (
                item
                for item in await store.list_place_categories()
                if item.slug == body.category
            ),
            None,
        )
        if category is None:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        resolved = resolve_maps_link(body.maps_url, request.app.state.maps_fetch)
        if resolved is None:
            raise HTTPException(status_code=400, detail="В ссылке нет координат")
        maps_url, latitude, longitude = resolved
        try:
            created = await store.create_place(
                name=body.name,
                category_id=category.id,
                google_place_id=None,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                partner_id=body.partner_id,
                is_active=body.is_active,
                blurb=body.blurb or None,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Это место уже есть") from None
        assets = await attach_place_photos(request, created.id, body.photos)
        return _place_payload(created, category.slug, assets)

    @app.patch("/api/places/{place_id}")
    async def update_place(
        request: Request,
        place_id: UUID,
        body: PlaceIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        store = _store(request)
        category = next(
            (
                item
                for item in await store.list_place_categories()
                if item.slug == body.category
            ),
            None,
        )
        if category is None:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        resolved = resolve_maps_link(body.maps_url, request.app.state.maps_fetch)
        if resolved is None:
            raise HTTPException(status_code=400, detail="В ссылке нет координат")
        maps_url, latitude, longitude = resolved
        try:
            updated = await store.update_place(
                place_id,
                name=body.name,
                category_id=category.id,
                google_place_id=None,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                partner_id=body.partner_id,
                is_active=body.is_active,
                blurb=body.blurb or None,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Место не найдено") from None
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Это место уже есть") from None
        assets = await store.list_place_assets(place_id)
        return _place_payload(updated, category.slug, assets)

    @app.get("/api/partners")
    async def list_partners(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        storage = request.app.state.storage
        return [partner_payload(item, storage) for item in await _store(request).list_partners()]

    @app.post("/api/partners", status_code=201)
    async def create_partner(
        request: Request,
        body: PartnerIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        created = await _store(request).create_partner(
            name=body.name,
            type=body.type,
            referral_url=body.referral_url,
            blurb=body.blurb,
            is_active=body.is_active,
            sort_order=body.sort_order,
        )
        return partner_payload(created, request.app.state.storage)

    @app.patch("/api/partners/{partner_id}")
    async def update_partner(
        request: Request,
        partner_id: UUID,
        body: PartnerIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        try:
            updated = await _store(request).update_partner(
                partner_id,
                name=body.name,
                type=body.type,
                referral_url=body.referral_url,
                blurb=body.blurb,
                is_active=body.is_active,
                sort_order=body.sort_order,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Партнёр не найден") from None
        return partner_payload(updated, request.app.state.storage)

    app.include_router(partner_logos_router)
    app.include_router(place_photos_router)
    app.include_router(partner_dashboard_router)
    return app
