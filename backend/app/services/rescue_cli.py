"""Implementa: RF-R1-09, RF-R1-10, RF-R1-11, RF-R1-12.

Lógica de los comandos de `bitacora-cli` (TASK-R1-011), separada de
`app/cli/main.py` para poder testearla igual que el resto de servicios
(fixture `db_session` contra PostgreSQL real) sin pasar por `CliRunner`.
Cada función que muta estado registra su acción en `audit_log` con
`actor="cli"` (RF-R1-12); ninguna incluye contraseñas en el detalle
auditado (RNF-R1-08 / CLAUDE.md).
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.security import hash_password, validate_password_policy
from app.models.account_lock import AccountLock
from app.models.audit_log import AuditLog
from app.models.session import Session as SessionModel
from app.models.user import User

TEMP_PASSWORD_BYTES = 18  # secrets.token_urlsafe produce ~1.3 caracteres por byte


class UserNotFoundError(ValueError):
    def __init__(self, username: str) -> None:
        super().__init__(f"No existe ningún usuario '{username}'")
        self.username = username


def _record_audit(db: DbSession, action: str, entity_id: str, detail: dict | None = None) -> None:
    db.add(AuditLog(actor="cli", action=action, entity="user", entity_id=entity_id, detail=detail))
    db.flush()


def _get_user_or_raise(db: DbSession, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise UserNotFoundError(username)
    return user


@dataclass
class UpsertResult:
    user: User
    created: bool


def create_or_reenable_user(
    db: DbSession, username: str, password: str, *, admin: bool = False
) -> UpsertResult:
    """Da de alta un usuario nuevo, o si ya existe (p. ej. estaba
    deshabilitado) lo rehabilita y le fija la contraseña interactiva
    indicada (RF-R1-10). El operador conoce la contraseña que acaba de
    teclear, así que no se fuerza cambio en el siguiente login.
    """
    validate_password_policy(password)
    role = "admin" if admin else "lector"
    user = db.scalar(select(User).where(User.username == username))

    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            must_change_password=False,
            disabled=False,
        )
        db.add(user)
        db.flush()
        _record_audit(db, "create-user", username, {"role": role, "rehabilitado": False})
        return UpsertResult(user=user, created=True)

    user.password_hash = hash_password(password)
    user.role = role
    user.disabled = False
    user.must_change_password = False
    db.flush()
    _record_audit(db, "create-user", username, {"role": role, "rehabilitado": True})
    return UpsertResult(user=user, created=False)


def reset_password(db: DbSession, username: str) -> str:
    """Genera y aplica una contraseña temporal, forzando cambio en el
    siguiente login (RF-R1-09). Devuelve la contraseña en claro para que
    la CLI la muestre una única vez por stdout; no se guarda en ningún
    sitio más.
    """
    user = _get_user_or_raise(db, username)

    temporary_password = secrets.token_urlsafe(TEMP_PASSWORD_BYTES)
    user.password_hash = hash_password(temporary_password)
    user.must_change_password = True
    db.flush()
    _record_audit(db, "reset-password", username)
    return temporary_password


def unlock_user(db: DbSession, username: str) -> bool:
    """Levanta cualquier bloqueo activo del usuario (RF-R1-11). Operación
    idempotente: no falla si no había ningún bloqueo (todavía no existe el
    enforcement de RF-R1-03 que los crearía — ver app/models/account_lock.py).
    """
    locks = db.scalars(select(AccountLock).where(AccountLock.username == username)).all()
    for lock in locks:
        db.delete(lock)
    db.flush()
    _record_audit(db, "unlock", username, {"bloqueos_levantados": len(locks)})
    return len(locks) > 0


def disable_user(db: DbSession, username: str) -> User:
    user = _get_user_or_raise(db, username)
    user.disabled = True
    db.flush()
    _record_audit(db, "disable", username)
    return user


def enable_user(db: DbSession, username: str) -> User:
    user = _get_user_or_raise(db, username)
    user.disabled = False
    db.flush()
    _record_audit(db, "enable", username)
    return user


def revoke_sessions(db: DbSession, username: str) -> int:
    user = _get_user_or_raise(db, username)
    sessions = db.scalars(
        select(SessionModel).where(SessionModel.user_id == user.id, SessionModel.revoked.is_(False))
    ).all()
    for session in sessions:
        session.revoked = True
    db.flush()
    _record_audit(db, "sessions-revoke", username, {"sesiones_revocadas": len(sessions)})
    return len(sessions)


@dataclass
class UserRow:
    username: str
    role: str
    disabled: bool
    locked_until: datetime | None
    last_login_at: datetime | None


def list_users(db: DbSession) -> list[UserRow]:
    """Solo lectura: no audita (RF-R1-11)."""
    now = datetime.now(timezone.utc)
    users = db.scalars(select(User).order_by(User.username)).all()
    rows = []
    for user in users:
        active_lock = db.scalar(
            select(AccountLock)
            .where(AccountLock.username == user.username, AccountLock.locked_until > now)
            .order_by(AccountLock.locked_until.desc())
        )
        rows.append(
            UserRow(
                username=user.username,
                role=user.role,
                disabled=user.disabled,
                locked_until=active_lock.locked_until if active_lock else None,
                last_login_at=user.last_login_at,
            )
        )
    return rows
