from __future__ import annotations

from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from admin_api.tokens import decode_access_token
from db.store import AdminUser, SessionStore

bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("role") == "partner_user":
            raise HTTPException(status_code=401, detail="Invalid token")
        email = str(payload["email"])
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Сессия истекла") from None
    except (jwt.PyJWTError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token") from None

    store: SessionStore = request.app.state.store
    admin = await store.get_admin_by_email(email)
    if admin is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return admin
