from __future__ import annotations

from typing import Optional
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from admin_api.deps import require_admin
from admin_api.tokens import decode_access_token
from db.store import AdminUser, SessionStore
from partner_dashboard.offers import record_referral_click
from partner_dashboard.store import (
    PartnerUser,
    authenticate_partner_user,
    create_partner_user,
    delete_partner_user,
    get_partner_stats,
    get_partner_user_by_email,
    has_partner_access,
    list_accessible_partners,
    list_partner_users,
    replace_partner_access,
    set_partner_user_password,
)
from partner_dashboard.tokens import create_partner_access_token

bearer_scheme = HTTPBearer(auto_error=False)

router = APIRouter()


class PartnerUserIn(BaseModel):
    email: EmailStr
    password: str
    partner_ids: list[UUID] = Field(min_length=1)


class PartnerUserPatch(BaseModel):
    password: Optional[str] = None
    partner_ids: Optional[list[UUID]] = None


class PartnerLoginRequest(BaseModel):
    email: EmailStr
    password: str


class PartnerLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _store(request: Request) -> SessionStore:
    return request.app.state.store


async def require_partner_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> PartnerUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("role") != "partner_user":
            raise HTTPException(status_code=401, detail="Invalid token")
        email = str(payload["email"])
    except HTTPException:
        raise
    except (jwt.PyJWTError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token") from None

    user = await get_partner_user_by_email(_store(request).pool, email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.post("/api/partner-users", status_code=201)
async def create_partner_user_route(
    request: Request,
    body: PartnerUserIn,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    if await _store(request).get_admin_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email уже используется")
    created = await create_partner_user(
        _store(request).pool,
        email=body.email,
        password=body.password,
        partner_ids=body.partner_ids,
    )
    return {"id": str(created.id), "email": created.email}


@router.get("/api/partner-users")
async def list_partner_users_route(
    request: Request,
    admin: AdminUser = Depends(require_admin),
) -> list[dict]:
    _ = admin
    return await list_partner_users(_store(request).pool)


@router.delete("/api/partner-users/{partner_user_id}", status_code=204)
async def delete_partner_user_route(
    request: Request,
    partner_user_id: UUID,
    admin: AdminUser = Depends(require_admin),
) -> None:
    _ = admin
    deleted = await delete_partner_user(_store(request).pool, partner_user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Пользователь не найден")


@router.patch("/api/partner-users/{partner_user_id}")
async def patch_partner_user_route(
    request: Request,
    partner_user_id: UUID,
    body: PartnerUserPatch,
    admin: AdminUser = Depends(require_admin),
) -> dict:
    _ = admin
    if body.partner_ids is None and body.password is None:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if body.partner_ids is not None:
        updated = await replace_partner_access(
            _store(request).pool,
            partner_user_id=partner_user_id,
            partner_ids=body.partner_ids,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    if body.password is not None:
        updated = await set_partner_user_password(
            _store(request).pool,
            partner_user_id=partner_user_id,
            password=body.password,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    partners = await list_accessible_partners(_store(request).pool, partner_user_id)
    return {"id": str(partner_user_id), "partners": partners}


@router.post("/api/partner/auth/login", response_model=PartnerLoginResponse)
async def partner_login(request: Request, body: PartnerLoginRequest) -> PartnerLoginResponse:
    user = authenticate_partner_user(
        await get_partner_user_by_email(_store(request).pool, body.email),
        body.password,
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not await list_accessible_partners(_store(request).pool, user.id):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_partner_access_token(partner_user_id=user.id, email=user.email)
    return PartnerLoginResponse(access_token=token)


@router.get("/api/partner/me")
async def partner_me(
    request: Request,
    user: PartnerUser = Depends(require_partner_user),
) -> dict:
    partners = await list_accessible_partners(_store(request).pool, user.id)
    return {"email": user.email, "partners": partners}


@router.get("/api/partner/stats")
async def partner_stats(
    request: Request,
    partner_id: UUID,
    user: PartnerUser = Depends(require_partner_user),
) -> dict:
    if not await has_partner_access(
        _store(request).pool, partner_user_id=user.id, partner_id=partner_id
    ):
        raise HTTPException(status_code=404, detail="Партнёр не найден")
    return await get_partner_stats(_store(request).pool, partner_id)


@router.get("/r/{token}")
async def follow_wrapped_offer(request: Request, token: str) -> RedirectResponse:
    url = await record_referral_click(_store(request).pool, token)
    if url is None:
        raise HTTPException(status_code=404, detail="Not found")
    return RedirectResponse(url=url, status_code=302)
