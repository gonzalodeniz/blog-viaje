"""Implementa: RF-R1-01, RF-R1-02, RF-R1-04."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
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

    assert result is not None
    assert result.id == user.id


@pytest.mark.spec("RF-R1-04")
def test_authenticate_con_password_incorrecta_devuelve_none(db_session, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")

    assert authenticate(db_session, "gonzalo", "password-equivocada") is None


@pytest.mark.spec("RF-R1-04")
def test_authenticate_con_usuario_inexistente_devuelve_none(db_session) -> None:
    assert authenticate(db_session, "no-existe", "cualquier-cosa") is None


@pytest.mark.spec("RF-R1-04")
def test_authenticate_con_cuenta_deshabilitada_devuelve_none(db_session, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123", disabled=True)

    assert authenticate(db_session, "gonzalo", "una-contraseña-larga-123") is None


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
