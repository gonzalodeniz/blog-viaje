"""Implementa: RF-R1-01, RF-R1-02, RF-R1-04, RNF-R1-03."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from app.api.deps import SESSION_COOKIE_NAME, get_current_user, require_csrf
from app.core.config import Settings, get_settings
from app.core.csrf import CSRF_COOKIE_NAME, generate_csrf_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth import authenticate, create_session, revoke_session

router = APIRouter(prefix="/api/auth", tags=["auth"])

GENERIC_LOGIN_ERROR = "Usuario o contraseña incorrectos"


class LoginRequest(BaseModel):
    username: str
    password: str
    remember: bool = False


def _set_auth_cookies(response: Response, *, session_token: str, settings: Settings, max_age: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=generate_csrf_token(),
        max_age=max_age,
        httponly=False,
        secure=True,
        samesite="lax",
        path="/",
    )


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    user = authenticate(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_LOGIN_ERROR)

    created = create_session(db, user, settings, remember=body.remember, ip=request.client.host if request.client else None)
    user.last_login_at = datetime.now(timezone.utc)

    ttl_seconds = int((created.session.expires_at - datetime.now(timezone.utc)).total_seconds())
    _set_auth_cookies(response, session_token=created.token, settings=settings, max_age=max(ttl_seconds, 0))

    return {"username": user.username}


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        revoke_session(db, token)

    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
    return {"status": "ok"}
