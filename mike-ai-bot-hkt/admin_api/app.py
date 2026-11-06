from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from admin_api.broadcasts import router as broadcasts_router
from admin_api.deps import require_admin
from admin_api.partner_logos import router as partner_logos_router
from admin_api.place_photos import (
    attach_place_photos,
    clear_place_photos,
    replace_place_photos,
)
from admin_api.place_photos import router as place_photos_router
from admin_api.passwords import verify_password
from admin_api.payloads import partner_payload
from knowledge_base import KnowledgeBaseEntry
from admin_api.tokens import create_access_token
from db.store import AdminUser, SessionStore
from db.url import resolve_database_url
from partner_dashboard.router import router as partner_dashboard_router
from maps_pin import follow_maps_redirect, resolve_maps_link
from partners import PartnerType
from tma_chat import (
    InvalidInitData,
    MikeUnavailable,
    ReplyInFlight,
    default_mike_model,
    history as tma_history,
    notify_admins,
    send as tma_send,
)
from tma_favourites import list_places as tma_favourite_places
from tma_favourites import list_saved as tma_list_saved
from tma_favourites import open_session as tma_open_session
from tma_favourites import save_partner as tma_save_partner
from tma_favourites import save_place as tma_save_place
from tma_offers import open_partner_offer as tma_open_partner_offer
from place_catalog import Place, PlaceAsset, PlaceCategory
from storage import AssetStorage
from topic_labels import labeled_topic_rows

PLACEHOLDER_COVER = "media/places/placeholder.jpg"


def _type_label(topic_label: str) -> str:
    text = topic_label.strip()
    while text and not text[0].isalnum():
        text = text[1:]
    return text.lstrip()


def _catalog_partner(partner, storage: AssetStorage | None) -> dict:
    logo = partner.logo_path or ""
    logo_url = storage.public_url(logo) if logo and storage is not None else logo
    return {
        "id": str(partner.id),
        "name": partner.name,
        "blurb": partner.blurb or "",
        "logo_url": logo_url,
        "sort_order": partner.sort_order,
    }


def _catalog_card(
    place: Place,
    category: str,
    photo_url: str,
    partner: dict | None = None,
) -> dict:
    return {
        "id": str(place.id),
        "name": place.name,
        "category": category,
        "blurb": place.blurb or "",
        "maps_url": place.maps_url or "",
        "photo_url": photo_url,
        "mike_recommends": place.mike_recommends,
        "partner": partner,
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TmaMessageIn(BaseModel):
    text: str


class KnowledgeBaseIn(BaseModel):
    partner_id: Optional[UUID] = None
    place_id: Optional[UUID] = None

    @model_validator(mode="after")
    def one_target(self):
        if (self.partner_id is None) == (self.place_id is None):
            raise ValueError("Укажите место или партнёра")
        return self


def _knowledge_base_payload(entry: KnowledgeBaseEntry) -> dict:
    return {
        "id": str(entry.id),
        "partner_id": None if entry.partner_id is None else str(entry.partner_id),
        "place_id": None if entry.place_id is None else str(entry.place_id),
        "name": entry.name,
        "kind": entry.kind,
        "blurb": entry.blurb,
        "referral_url": entry.referral_url,
        "maps_url": entry.maps_url,
        "in_chat": entry.is_visible,
    }


class FavouriteIn(BaseModel):
    saved: bool


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
    choice_phrase: str

    @field_validator("choice_phrase")
    @classmethod
    def choice_phrase_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("choice_phrase is required")
        return stripped


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
    mike_recommends: bool = False
    photos: Optional[List[PlacePhotoIn]] = None


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
    place: Place,
    category_slug: str,
    assets: list[PlaceAsset] | None = None,
    storage: AssetStorage | None = None,
) -> dict:
    photos = []
    for asset in assets or ():
        photo = {"id": str(asset.id), "path": asset.path}
        if storage is not None:
            photo["url"] = storage.public_url(asset.path)
        photos.append(photo)
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
        "mike_recommends": place.mike_recommends,
        "photos": photos,
        "cover": photos[0]["path"] if photos else PLACEHOLDER_COVER,
    }


_FROM_ENV = object()


def create_app(
    *,
    store: SessionStore | None = None,
    storage: AssetStorage | None | object = _FROM_ENV,
    maps_fetch=None,
    mike_model=None,
    notify_lead=None,
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
    app.state.mike_model = mike_model
    app.state.notify_lead = notify_admins if notify_lead is None else notify_lead

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
                _place_payload(
                    place,
                    categories[place.category_id],
                    assets,
                    request.app.state.storage,
                )
            )
        return payloads

    @app.get("/api/catalog/places")
    async def list_catalog_places(request: Request) -> list[dict]:
        store = _store(request)
        categories = {item.id: item.label for item in await store.list_place_categories()}
        partners = {item.id: item for item in await store.list_partners()}
        storage = request.app.state.storage
        payloads = []
        for place in await store.list_visible_places():
            assets = await store.list_place_assets(place.id)
            cover = assets[0].path if assets else PLACEHOLDER_COVER
            photo_url = storage.public_url(cover) if storage is not None else cover
            bound = partners.get(place.partner_id) if place.partner_id else None
            partner = _catalog_partner(bound, storage) if bound is not None else None
            payloads.append(
                _catalog_card(place, categories[place.category_id], photo_url, partner)
            )
        return payloads

    @app.get("/api/catalog/partners")
    async def list_catalog_partners(request: Request) -> list[dict]:
        store = _store(request)
        types = {item.slug: item for item in await store.list_partner_types()}
        storage = request.app.state.storage
        payloads = []
        for partner in await store.list_partners():
            if not partner.is_active:
                continue
            card = _catalog_partner(partner, storage)
            card["type_label"] = _type_label(types[partner.type].topic_label)
            payloads.append(card)
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
                mike_recommends=body.mike_recommends,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Это место уже есть") from None
        assets = await attach_place_photos(request, created.id, body.photos or [])
        return _place_payload(created, category.slug, assets, request.app.state.storage)

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
                mike_recommends=body.mike_recommends,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Место не найдено") from None
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Это место уже есть") from None
        if body.photos is None:
            assets = await store.list_place_assets(place_id)
        elif body.photos:
            assets = await replace_place_photos(request, place_id, body.photos)
        else:
            assets = await clear_place_photos(request, place_id)
        return _place_payload(updated, category.slug, assets, request.app.state.storage)

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

    @app.get("/api/knowledge-base")
    async def list_knowledge_base(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        entries = await _store(request).list_knowledge_base()
        return [_knowledge_base_payload(entry) for entry in entries]

    @app.post("/api/knowledge-base", status_code=201)
    async def add_knowledge_base_entry(
        request: Request,
        body: KnowledgeBaseIn,
        admin: AdminUser = Depends(require_admin),
    ) -> dict:
        _ = admin
        store = _store(request)
        try:
            if body.place_id is not None:
                if await store.place_partner_is_in_knowledge_base(body.place_id):
                    raise HTTPException(status_code=409, detail="Уже в базе знаний")
                entry = await store.add_knowledge_base_place(body.place_id)
            else:
                partner_id = body.partner_id
                assert partner_id is not None
                if await store.partner_place_is_in_knowledge_base(partner_id):
                    raise HTTPException(status_code=409, detail="Уже в базе знаний")
                entry = await store.add_knowledge_base_partner(partner_id)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Уже в базе знаний") from None
        return _knowledge_base_payload(entry)

    @app.delete("/api/knowledge-base/{entry_id}", status_code=204)
    async def delete_knowledge_base_entry(
        request: Request,
        entry_id: UUID,
        admin: AdminUser = Depends(require_admin),
    ) -> None:
        _ = admin
        await _store(request).delete_knowledge_base_entry(entry_id)

    def _tma_init_data(authorization: Optional[str]) -> str:
        if not authorization or not authorization.startswith("tma "):
            raise HTTPException(status_code=401, detail="unauthorized")
        return authorization[4:].strip()

    def _bot_token() -> str:
        return os.environ.get("TELEGRAM_BOT_TOKEN") or ""

    @app.get("/api/tma/messages")
    async def list_tma_messages(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            messages = await tma_history(
                _store(request),
                init_data=_tma_init_data(authorization),
                bot_token=_bot_token(),
            )
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None
        return {"messages": messages}

    @app.post("/api/tma/messages")
    async def create_tma_message(
        request: Request,
        body: TmaMessageIn,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        model = request.app.state.mike_model or default_mike_model
        try:
            reply = await tma_send(
                _store(request),
                model,
                init_data=_tma_init_data(authorization),
                bot_token=_bot_token(),
                text=body.text,
                notify=request.app.state.notify_lead,
            )
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None
        except MikeUnavailable:
            raise HTTPException(status_code=502, detail="mike unavailable") from None
        except ReplyInFlight:
            raise HTTPException(status_code=409, detail="reply in flight") from None
        return {"reply": reply}

    @app.post("/api/tma/session", status_code=204)
    async def open_tma_session(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ) -> None:
        try:
            await tma_open_session(
                _store(request),
                init_data=_tma_init_data(authorization),
                bot_token=_bot_token(),
            )
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None

    @app.post("/api/tma/partners/{partner_id}/offer")
    async def create_tma_partner_offer(
        request: Request,
        partner_id: UUID,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            return await tma_open_partner_offer(
                _store(request),
                init_data=_tma_init_data(authorization),
                bot_token=_bot_token(),
                partner_id=partner_id,
                public_base=os.environ.get("PARTNER_OFFER_BASE_URL", ""),
            )
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None
        except KeyError:
            raise HTTPException(status_code=404, detail="Партнёр не найден") from None

    @app.get("/api/tma/favourites")
    async def list_tma_favourites(
        request: Request,
        authorization: Optional[str] = Header(default=None),
    ) -> list[dict]:
        store = _store(request)
        try:
            init_data = _tma_init_data(authorization)
            bot_token = _bot_token()
            saved = await tma_list_saved(store, init_data=init_data, bot_token=bot_token)
            places = {
                place.id: place
                for place in await tma_favourite_places(
                    store,
                    init_data=init_data,
                    bot_token=bot_token,
                )
            }
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None
        categories = {item.id: item.label for item in await store.list_place_categories()}
        partners = {item.id: item for item in await store.list_partners()}
        types = {item.slug: item for item in await store.list_partner_types()}
        storage = request.app.state.storage
        payloads = []
        for kind, item_id in saved:
            if kind == "place":
                place = places.get(item_id)
                if place is None:
                    continue
                assets = await store.list_place_assets(place.id)
                cover = assets[0].path if assets else PLACEHOLDER_COVER
                photo_url = storage.public_url(cover) if storage is not None else cover
                card = _catalog_card(place, categories[place.category_id], photo_url)
                card["kind"] = "place"
                payloads.append(card)
                continue
            partner = partners.get(item_id)
            if partner is None or not partner.is_active:
                continue
            logo = partner.logo_path or ""
            logo_url = storage.public_url(logo) if logo and storage is not None else logo
            payloads.append(
                {
                    "kind": "partner",
                    "id": str(partner.id),
                    "name": partner.name,
                    "type_label": _type_label(types[partner.type].topic_label),
                    "blurb": partner.blurb or "",
                    "logo_url": logo_url,
                }
            )
        return payloads

    @app.put("/api/tma/favourites/partners/{partner_id}")
    async def set_tma_partner_favourite(
        request: Request,
        partner_id: UUID,
        body: FavouriteIn,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            saved = await tma_save_partner(
                _store(request),
                init_data=_tma_init_data(authorization),
                bot_token=_bot_token(),
                partner_id=partner_id,
                saved=body.saved,
            )
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None
        return {"saved": saved}

    @app.put("/api/tma/favourites/{place_id}")
    async def set_tma_favourite(
        request: Request,
        place_id: UUID,
        body: FavouriteIn,
        authorization: Optional[str] = Header(default=None),
    ) -> dict:
        try:
            saved = await tma_save_place(
                _store(request),
                init_data=_tma_init_data(authorization),
                bot_token=_bot_token(),
                place_id=place_id,
                saved=body.saved,
            )
        except InvalidInitData:
            raise HTTPException(status_code=401, detail="unauthorized") from None
        return {"saved": saved}

    app.include_router(broadcasts_router)
    app.include_router(partner_logos_router)
    app.include_router(place_photos_router)
    app.include_router(partner_dashboard_router)
    return app
