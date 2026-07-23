"""Implementa: RF-R1-01, RF-R1-02, RF-R1-04.

Servicio de autenticación: verificación de credenciales y ciclo de vida de
la sesión (creación, resolución con expiración deslizante + tope absoluto,
revocación). No incluye bloqueo por intentos fallidos (RF-R1-03/04
completo) ni roles (RF-R1-07): esos llegan en una tarea posterior de
WP-R1-2 (ver tasks/R1/TASK-R1-007.md).
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.config import Settings
from app.core.security import verify_dummy_password, verify_password
from app.models.session import Session as SessionModel
from app.models.user import User

SESSION_TOKEN_BYTES = 32  # 256 bits


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def authenticate(db: DbSession, username: str, password: str) -> User | None:
    """Verifica credenciales. Devuelve None tanto si el usuario no existe,
    la contraseña es incorrecta o la cuenta está deshabilitada — nunca se
    distingue el motivo (RF-R1-04), ni siquiera por el tiempo de respuesta.
    """
    user = db.scalar(select(User).where(User.username == username))

    if user is None:
        verify_dummy_password()
        return None

    if not verify_password(password, user.password_hash):
        return None

    if user.disabled:
        return None

    return user


@dataclass
class CreatedSession:
    session: SessionModel
    token: str


def create_session(
    db: DbSession,
    user: User,
    settings: Settings,
    *,
    remember: bool,
    ip: str | None = None,
) -> CreatedSession:
    now = datetime.now(timezone.utc)
    ttl = (
        timedelta(days=settings.session_remember_days)
        if remember
        else timedelta(hours=settings.session_ttl_hours)
    )
    absolute_expires_at = now + timedelta(days=settings.session_absolute_max_days)

    token = secrets.token_urlsafe(SESSION_TOKEN_BYTES)
    session = SessionModel(
        user_id=user.id,
        token_hash=_hash_token(token),
        expires_at=min(now + ttl, absolute_expires_at),
        absolute_expires_at=absolute_expires_at,
        remember=remember,
        ip=ip,
    )
    db.add(session)
    db.flush()
    return CreatedSession(session=session, token=token)


def resolve_session(db: DbSession, token: str, settings: Settings) -> User | None:
    """Devuelve el usuario de una sesión válida y extiende su expiración
    deslizante (sin superar nunca `absolute_expires_at`). Devuelve None si
    el token no corresponde a ninguna sesión activa y no vencida.
    """
    session = db.scalar(select(SessionModel).where(SessionModel.token_hash == _hash_token(token)))
    if session is None or session.revoked:
        return None

    now = datetime.now(timezone.utc)
    if now >= session.expires_at or now >= session.absolute_expires_at:
        return None

    user = db.get(User, session.user_id)
    if user is None or user.disabled:
        return None

    ttl = (
        timedelta(days=settings.session_remember_days)
        if session.remember
        else timedelta(hours=settings.session_ttl_hours)
    )
    session.last_seen_at = now
    session.expires_at = min(now + ttl, session.absolute_expires_at)
    db.flush()
    return user


def revoke_session(db: DbSession, token: str) -> None:
    session = db.scalar(select(SessionModel).where(SessionModel.token_hash == _hash_token(token)))
    if session is not None:
        session.revoked = True
        db.flush()
