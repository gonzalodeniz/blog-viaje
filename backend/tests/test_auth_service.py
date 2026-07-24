"""Implementa: RF-R1-01, RF-R1-02, RF-R1-04."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from sqlalchemy import select

from app.core.config import Settings
from app.models.account_lock import AccountLock
from app.models.login_attempt import LoginAttempt, LoginAttemptResult
from app.models.session import Session as SessionModel
from app.models.user import User
from app.services.auth import authenticate, create_session, resolve_session, revoke_session


def _settings(**overrides: object) -> Settings:
    defaults = {"session_ttl_hours": 24, "session_remember_days": 30, "session_absolute_max_days": 90}
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.mark.spec("RF-R1-01")
def test_authenticate_con_credenciales_correctas(db_session, make_user) -> None:
    user = make_user(username="gonzalo", password="una-contraseña-larga-123")

    result = authenticate(db_session, "gonzalo", "una-contraseña-larga-123")

    assert result.user is not None
    assert result.user.id == user.id
    assert result.locked_until is None


@pytest.mark.spec("RF-R1-04")
def test_authenticate_con_password_incorrecta_devuelve_usuario_none(db_session, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")

    result = authenticate(db_session, "gonzalo", "password-equivocada")

    assert result.user is None
    assert result.locked_until is None


@pytest.mark.spec("RF-R1-04")
def test_authenticate_con_usuario_inexistente_devuelve_usuario_none(db_session) -> None:
    result = authenticate(db_session, "no-existe", "cualquier-cosa")

    assert result.user is None
    assert result.locked_until is None


@pytest.mark.spec("RF-R1-04")
def test_authenticate_con_cuenta_deshabilitada_devuelve_usuario_none(db_session, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123", disabled=True)

    result = authenticate(db_session, "gonzalo", "una-contraseña-larga-123")

    assert result.user is None


@pytest.mark.spec("RF-R1-03")
def test_authenticate_bloquea_tras_5_fallos_consecutivos(db_session, make_user) -> None:
    make_user(username="gonzalo", password="S3gura!Larga")

    for _ in range(5):
        authenticate(db_session, "gonzalo", "incorrecta")

    # El 6.º intento se bloquea aunque la contraseña sea correcta.
    result = authenticate(db_session, "gonzalo", "S3gura!Larga")

    assert result.user is None
    assert result.locked_until is not None
    remaining = (result.locked_until - datetime.now(timezone.utc)).total_seconds()
    assert 14 * 60 < remaining <= 15 * 60


@pytest.mark.spec("RF-R1-03")
def test_authenticate_login_correcto_reinicia_el_contador(db_session, make_user) -> None:
    make_user(username="gonzalo", password="S3gura!Larga")

    for _ in range(4):
        authenticate(db_session, "gonzalo", "incorrecta")
    authenticate(db_session, "gonzalo", "S3gura!Larga")

    # Tras el login correcto, 4 fallos más no deberían bloquear (el
    # contador se reinició); hacen falta 5 fallos *después* del éxito.
    for _ in range(4):
        result = authenticate(db_session, "gonzalo", "incorrecta")

    assert result.locked_until is None
    assert db_session.scalar(select(AccountLock).where(AccountLock.username == "gonzalo")) is None


@pytest.mark.spec("RF-R1-03")
def test_authenticate_backoff_exponencial_en_segundo_bloqueo(db_session, make_user) -> None:
    make_user(username="gonzalo", password="S3gura!Larga")

    for _ in range(5):
        authenticate(db_session, "gonzalo", "incorrecta")

    lock = db_session.scalar(select(AccountLock).where(AccountLock.username == "gonzalo"))
    assert lock.consecutive_locks == 1

    # Simula que la ventana de bloqueo ya expiró (sin login correcto de por
    # medio, así que el nivel de backoff no se reinicia) y se repite el
    # patrón de 5 fallos.
    lock.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.flush()

    for _ in range(5):
        result = authenticate(db_session, "gonzalo", "incorrecta")

    assert result.locked_until is not None
    remaining = (result.locked_until - datetime.now(timezone.utc)).total_seconds()
    assert 29 * 60 < remaining <= 30 * 60

    db_session.refresh(lock)
    assert lock.consecutive_locks == 2


@pytest.mark.spec("RF-R1-03")
def test_authenticate_login_correcto_borra_un_bloqueo_ya_expirado(db_session, make_user) -> None:
    make_user(username="gonzalo", password="S3gura!Larga")
    db_session.add(
        AccountLock(
            username="gonzalo",
            locked_until=datetime.now(timezone.utc) - timedelta(seconds=1),
            consecutive_locks=2,
        )
    )
    db_session.flush()

    result = authenticate(db_session, "gonzalo", "S3gura!Larga")

    assert result.user is not None
    assert db_session.scalar(select(AccountLock).where(AccountLock.username == "gonzalo")) is None


@pytest.mark.spec("RF-R1-03")
def test_authenticate_backoff_tiene_tope_de_60_minutos(db_session, make_user) -> None:
    make_user(username="gonzalo", password="S3gura!Larga")
    # 4 bloqueos previos ya acumulados (15 -> 30 -> 60 -> 60, el 4.º ya
    # tocaría 120 sin el tope): el 5.º debe seguir capado a 60 min.
    db_session.add(
        AccountLock(
            username="gonzalo",
            locked_until=datetime.now(timezone.utc) - timedelta(seconds=1),
            consecutive_locks=4,
        )
    )
    db_session.flush()

    for _ in range(5):
        authenticate(db_session, "gonzalo", "incorrecta")
    # El 5.º fallo dispara el bloqueo puertas adentro, pero (igual que en
    # el escenario Gherkin de RF-R1-03) es el intento *siguiente* el que lo
    # revela en el resultado.
    result = authenticate(db_session, "gonzalo", "incorrecta")

    remaining = (result.locked_until - datetime.now(timezone.utc)).total_seconds()
    assert remaining <= 60 * 60 + 1


@pytest.mark.spec("RF-R1-05")
def test_authenticate_registra_todos_los_intentos_con_ip_y_user_agent(db_session, make_user) -> None:
    # No se ordena por created_at: dentro de la misma transacción de test,
    # func.now() en Postgres devuelve el mismo valor para todos los INSERT
    # (es el timestamp de inicio de la transacción, no del statement), así
    # que el orden de inserción no es reconstruible por esa columna aquí.
    make_user(username="gonzalo", password="S3gura!Larga")

    authenticate(db_session, "gonzalo", "incorrecta", ip="203.0.113.7", user_agent="pytest-agent")
    authenticate(db_session, "gonzalo", "S3gura!Larga", ip="203.0.113.7", user_agent="pytest-agent")

    attempts = db_session.scalars(
        select(LoginAttempt).where(LoginAttempt.username_claimed == "gonzalo")
    ).all()

    assert sorted(a.result for a in attempts) == sorted([LoginAttemptResult.FAILURE, LoginAttemptResult.SUCCESS])
    assert all(a.ip == "203.0.113.7" and a.user_agent == "pytest-agent" for a in attempts)


@pytest.mark.spec("RF-R1-05")
def test_authenticate_registra_intento_bloqueado_como_locked(db_session, make_user) -> None:
    make_user(username="gonzalo", password="S3gura!Larga")
    for _ in range(5):
        authenticate(db_session, "gonzalo", "incorrecta")

    authenticate(db_session, "gonzalo", "S3gura!Larga")

    locked_attempts = db_session.scalars(
        select(LoginAttempt).where(
            LoginAttempt.username_claimed == "gonzalo", LoginAttempt.result == LoginAttemptResult.LOCKED
        )
    ).all()
    assert len(locked_attempts) == 1


@pytest.mark.spec("RF-R1-02")
def test_create_session_genera_token_y_registro(db_session, make_user) -> None:
    user = make_user()

    created = create_session(db_session, user, _settings(), remember=False)

    assert len(created.token) > 20
    assert created.session.user_id == user.id
    assert created.session.remember is False


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_devuelve_el_usuario_de_un_token_valido(db_session, make_user) -> None:
    user = make_user()
    created = create_session(db_session, user, _settings(), remember=False)

    resolved = resolve_session(db_session, created.token, _settings())

    assert resolved is not None
    assert resolved.id == user.id


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_con_token_invalido_devuelve_none(db_session) -> None:
    assert resolve_session(db_session, "token-que-no-existe", _settings()) is None


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_extiende_la_expiracion_deslizante(db_session, make_user) -> None:
    user = make_user()
    settings = _settings(session_ttl_hours=24)
    created = create_session(db_session, user, settings, remember=False)
    original_expiry = created.session.expires_at

    # Simula el paso del tiempo retrasando manualmente expires_at/last_seen_at,
    # como si la sesión llevara un rato inactiva antes de la siguiente petición.
    created.session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.flush()

    resolve_session(db_session, created.token, settings)
    db_session.flush()

    assert created.session.expires_at > datetime.now(timezone.utc) + timedelta(hours=1)
    assert created.session.expires_at != original_expiry


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_respeta_el_tope_absoluto(db_session, make_user) -> None:
    user = make_user()
    settings = _settings(session_ttl_hours=24, session_absolute_max_days=90)
    created = create_session(db_session, user, settings, remember=False)

    # El tope absoluto de la sesión está a punto de cumplirse (antes de lo
    # que tardaría en vencer el TTL deslizante de 24h): la renovación no
    # debe superarlo.
    created.session.absolute_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    created.session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db_session.flush()

    resolve_session(db_session, created.token, settings)
    db_session.flush()

    assert created.session.expires_at == created.session.absolute_expires_at


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_expirada_devuelve_none(db_session, make_user) -> None:
    user = make_user()
    settings = _settings()
    created = create_session(db_session, user, settings, remember=False)
    created.session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.flush()

    assert resolve_session(db_session, created.token, settings) is None


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_revocada_devuelve_none(db_session, make_user) -> None:
    user = make_user()
    settings = _settings()
    created = create_session(db_session, user, settings, remember=False)

    revoke_session(db_session, created.token)

    assert resolve_session(db_session, created.token, settings) is None


@pytest.mark.spec("RF-R1-02")
def test_resolve_session_con_remember_usa_ttl_largo(db_session, make_user) -> None:
    user = make_user()
    settings = _settings(session_ttl_hours=24, session_remember_days=30, session_absolute_max_days=90)
    created = create_session(db_session, user, settings, remember=True)
    created.session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db_session.flush()

    resolve_session(db_session, created.token, settings)
    db_session.flush()

    # Con remember=True la renovación usa 30 días, no las 24h del TTL corto.
    assert created.session.expires_at > datetime.now(timezone.utc) + timedelta(days=20)


@pytest.mark.spec("RF-R1-02")
def test_username_es_unico(db_session, make_user) -> None:
    make_user(username="gonzalo")

    with pytest.raises(IntegrityError):
        db_session.add(User(username="gonzalo", password_hash="x"))
        db_session.flush()


@pytest.mark.spec("RF-R1-02")
def test_borrar_usuario_hace_cascade_sobre_sus_sesiones(db_session, make_user) -> None:
    user = make_user()
    created = create_session(db_session, user, _settings(), remember=False)
    session_id = created.session.id

    db_session.delete(user)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(SessionModel, session_id) is None
