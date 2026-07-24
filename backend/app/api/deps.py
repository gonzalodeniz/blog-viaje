"""Implementa: RF-R1-01, RF-R1-07, RNF-R1-03.

Dependencias de FastAPI compartidas: usuario autenticado a partir de la
cookie de sesión, y verificación CSRF para mutaciones que dependen de ella.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app.core.config import Settings, get_settings
from app.core.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, csrf_token_matches
from app.db.session import get_db
from app.models.user import User
from app.services.auth import resolve_session

SESSION_COOKIE_NAME = "session"


def get_current_user(
    request: Request,
    db: DbSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    user = resolve_session(db, token, settings) if token else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user


def require_csrf(request: Request) -> None:
    cookie_value = request.cookies.get(CSRF_COOKIE_NAME)
    header_value = request.headers.get(CSRF_HEADER_NAME)
    if not csrf_token_matches(cookie_value, header_value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token CSRF inválido")


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol admin")
    return current_user
