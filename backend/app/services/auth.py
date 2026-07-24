"""Implementa: RF-R1-01, RF-R1-02, RF-R1-03, RF-R1-04, RF-R1-05.

Servicio de autenticación: verificación de credenciales, bloqueo temporal
por intentos fallidos con backoff exponencial, registro de todos los
intentos, y ciclo de vida de la sesión (creación, resolución con
expiración deslizante + tope absoluto, revocación). No incluye roles
(RF-R1-07, ya cubierto por app.api.deps.require_admin).
"""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from app.core.config import Settings
from app.core.security import verify_dummy_password, verify_password
from app.models.account_lock import AccountLock
from app.models.login_attempt import LoginAttempt, LoginAttemptResult
from app.models.session import Session as SessionModel
from app.models.user import User

SESSION_TOKEN_BYTES = 32  # 256 bits

# RF-R1-03: 5 fallos consecutivos en ventana de 15 min -> bloqueo con
# backoff exponencial 15 -> 30 -> 60 min (tope 60), ver SPEC-MASTER §8.
LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW = timedelta(minutes=15)
BASE_LOCKOUT_MINUTES = 15
MAX_LOCKOUT_MINUTES = 60


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class AuthResult:
    user: User | None
    # Presente solo si la cuenta está bloqueada ahora mismo; el mensaje al
    # exterior puede incluirlo sin revelar si el usuario existe (RF-R1-04):
    # cualquier username_claimed puede acumular intentos y bloquearse igual.
    locked_until: datetime | None = None


def _record_attempt(
    db: DbSession,
    username: str,
    result: LoginAttemptResult,
    now: datetime,
    *,
    ip: str | None,
    user_agent: str | None,
) -> None:
    # created_at se fija explícitamente con el reloj de aplicación en vez
    # de dejar el server_default=func.now(): dentro de una misma
    # transacción, Postgres devuelve el mismo now() para todos los INSERT
    # (es el instante de inicio de la transacción, no del statement), lo
    # que haría indistinguibles varios intentos consecutivos y rompería el
    # cálculo de la ventana deslizante de _register_failure.
    db.add(
        LoginAttempt(
            username_claimed=username, result=result, ip=ip, user_agent=user_agent, created_at=now
        )
    )
    db.flush()


def _register_failure(db: DbSession, username: str, now: datetime) -> None:
    """Cuenta los fallos consecutivos desde el último éxito (o desde el
    principio de la ventana de 15 min, lo que sea más reciente) y, al
    llegar al 5.º, crea o intensifica el bloqueo con backoff exponencial.
    """
    last_success = db.scalar(
        select(func.max(LoginAttempt.created_at)).where(
            LoginAttempt.username_claimed == username,
            LoginAttempt.result == LoginAttemptResult.SUCCESS,
        )
    )
    window_start = now - LOCKOUT_WINDOW
    conditions = [
        LoginAttempt.username_claimed == username,
        LoginAttempt.result == LoginAttemptResult.FAILURE,
        LoginAttempt.created_at >= window_start,
    ]
    # Estrictamente posterior al último éxito (no >=): un fallo no puede
    # compartir instante con el éxito que se supone que lo reinicia.
    if last_success is not None:
        conditions.append(LoginAttempt.created_at > last_success)

    recent_failures = db.scalar(
        select(func.count()).select_from(LoginAttempt).where(*conditions
        )
    )
    # El fallo actual ya está en login_attempts: _record_attempt hace
    # flush() antes de llamar aquí, así que este SELECT ya lo cuenta.
    if recent_failures < LOCKOUT_THRESHOLD:
        return

    existing_lock = db.scalar(select(AccountLock).where(AccountLock.username == username))
    consecutive = (existing_lock.consecutive_locks + 1) if existing_lock else 1
    minutes = min(BASE_LOCKOUT_MINUTES * (2 ** (consecutive - 1)), MAX_LOCKOUT_MINUTES)
    locked_until = now + timedelta(minutes=minutes)

    if existing_lock:
        existing_lock.locked_until = locked_until
        existing_lock.consecutive_locks = consecutive
    else:
        db.add(AccountLock(username=username, locked_until=locked_until, consecutive_locks=consecutive))
    db.flush()


def authenticate(
    db: DbSession,
    username: str,
    password: str,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuthResult:
    """Verifica credenciales. `AuthResult.user` es None tanto si el usuario
    no existe, la contraseña es incorrecta o la cuenta está deshabilitada
    — nunca se distingue el motivo (RF-R1-04), ni siquiera por el tiempo de
    respuesta. Si la cuenta está bloqueada (RF-R1-03), tampoco se comprueba
    la contraseña: se devuelve `locked_until` sin más.
    """
    now = datetime.now(timezone.utc)

    lock = db.scalar(select(AccountLock).where(AccountLock.username == username))
    if lock is not None and lock.locked_until > now:
        _record_attempt(db, username, LoginAttemptResult.LOCKED, now, ip=ip, user_agent=user_agent)
        # commit explícito: el endpoint de login (app/api/auth.py) lanza un
        # HTTPException justo después de esto para el 401, y ese
        # HTTPException se propaga a través de la dependencia get_db()
        # (app/db/session.py), cuyo bloque `except Exception: db.rollback()`
        # descartaría el intento recién registrado si se dejara solo en
        # flush(). El registro de auditoría debe sobrevivir aunque la
        # petición termine en error — no es parte de esa transacción de
        # negocio, es la constancia de que la transacción se intentó.
        db.commit()
        return AuthResult(user=None, locked_until=lock.locked_until)

    user = db.scalar(select(User).where(User.username == username))

    if user is None:
        verify_dummy_password()
        _record_attempt(db, username, LoginAttemptResult.FAILURE, now, ip=ip, user_agent=user_agent)
        _register_failure(db, username, now)
        db.commit()  # ver comentario arriba: sobrevive al 401 que sigue
        return AuthResult(user=None)

    if not verify_password(password, user.password_hash) or user.disabled:
        _record_attempt(db, username, LoginAttemptResult.FAILURE, now, ip=ip, user_agent=user_agent)
        _register_failure(db, username, now)
        db.commit()  # ver comentario arriba: sobrevive al 401 que sigue
        return AuthResult(user=None)

    # Login correcto: reinicia el contador de fallos y el nivel de backoff
    # (SPEC-MASTER §8: "un login correcto pone consecutive_locks a 0").
    if lock is not None:
        db.delete(lock)
    _record_attempt(db, username, LoginAttemptResult.SUCCESS, now, ip=ip, user_agent=user_agent)
    return AuthResult(user=user)


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
