from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Optional
from uuid import UUID

import asyncpg
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr

from admin_api.passwords import verify_password
from admin_api.tokens import create_access_token, decode_access_token
from db.store import AdminUser, SessionStore
from db.url import resolve_database_url
from partners import Partner, PartnerType
from topic_labels import labeled_topic_rows

bearer_scheme = HTTPBearer(auto_error=False)


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


class PartnerIn(BaseModel):
    name: str
    type: str
    referral_url: str
    blurb: str = ""
    is_active: bool = True
    sort_order: int = 0


async def require_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        email = str(payload["email"])
    except (jwt.PyJWTError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token") from None

    store: SessionStore = request.app.state.store
    admin = await store.get_admin_by_email(email)
    if admin is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return admin


def _partner_type_payload(partner_type: PartnerType) -> dict:
    return asdict(partner_type)


def _partner_payload(partner: Partner) -> dict:
    payload = asdict(partner)
    payload["id"] = str(partner.id)
    payload["logo_path"] = partner.logo_path or ""
    payload["blurb"] = partner.blurb or ""
    return payload


def create_app(*, store: SessionStore | None = None) -> FastAPI:
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
    async def list_partner_types(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        return [_partner_type_payload(item) for item in await _store(request).list_partner_types()]

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

    @app.get("/api/partners")
    async def list_partners(
        request: Request,
        admin: AdminUser = Depends(require_admin),
    ) -> list[dict]:
        _ = admin
        return [_partner_payload(item) for item in await _store(request).list_partners()]

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
        return _partner_payload(created)

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
        return _partner_payload(updated)

    return app
