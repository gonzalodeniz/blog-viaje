"""Implementa: RF-R1-08, RF-R1-09, RF-R1-10, RF-R1-11, RF-R1-12."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from typer.testing import CliRunner

import app.cli.main as cli_main
from app.cli.main import app
from app.core.security import verify_password
from app.models.account_lock import AccountLock
from app.models.audit_log import AuditLog
from app.models.session import Session as SessionModel
from app.models.user import User

runner = CliRunner()


@pytest.fixture
def invoke(db_session, monkeypatch):
    """Redirige la sesión de BD que usan los comandos a la del test (misma
    transacción, revertida al terminar), igual que la fixture `client` hace
    con `app.dependency_overrides` para la API HTTP.
    """

    @contextmanager
    def _fake_session():
        yield db_session

    monkeypatch.setattr(cli_main, "_session", _fake_session)

    def _invoke(args: list[str], input: str | None = None):
        return runner.invoke(app, args, input=input)

    return _invoke


def _audit_actions(db_session, entity_id: str) -> list[str]:
    rows = db_session.scalars(
        select(AuditLog).where(AuditLog.entity == "user", AuditLog.entity_id == entity_id)
    ).all()
    return [row.action for row in rows]


@pytest.mark.spec("RF-R1-08")
def test_cli_no_se_expone_por_http() -> None:
    """`bitacora-cli` no es un router FastAPI ni está montado en la app: solo
    es alcanzable ejecutándolo directamente en una shell del servidor.
    """
    import typer

    from app.main import app as http_app

    assert isinstance(cli_main.app, typer.Typer)
    http_paths = {getattr(route, "path", "") for route in http_app.routes}
    assert not any("cli" in path for path in http_paths)


@pytest.mark.spec("RNF-R1-07")
def test_cli_version_se_ejecuta() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "bitacora-cli" in result.stdout


@pytest.mark.spec("RF-R1-10")
def test_create_user_da_de_alta_con_contrasena_interactiva(invoke, db_session) -> None:
    result = invoke(["create-user", "nueva"], input="una-contraseña-larga-123\nuna-contraseña-larga-123\n")

    assert result.exit_code == 0, result.output
    user = db_session.scalar(select(User).where(User.username == "nueva"))
    assert user is not None
    assert user.role == "lector"
    assert user.disabled is False
    assert verify_password("una-contraseña-larga-123", user.password_hash)
    assert "create-user" in _audit_actions(db_session, "nueva")


@pytest.mark.spec("RF-R1-10")
def test_create_user_con_admin_asigna_rol_admin(invoke, db_session) -> None:
    result = invoke(
        ["create-user", "jefa", "--admin"], input="una-contraseña-larga-123\nuna-contraseña-larga-123\n"
    )

    assert result.exit_code == 0, result.output
    user = db_session.scalar(select(User).where(User.username == "jefa"))
    assert user.role == "admin"


@pytest.mark.spec("RF-R1-10")
def test_create_user_rehabilita_usuario_deshabilitado(invoke, db_session, make_user) -> None:
    make_user(username="vuelve", disabled=True)

    result = invoke(
        ["create-user", "vuelve"], input="otra-contraseña-larga-456\notra-contraseña-larga-456\n"
    )

    assert result.exit_code == 0, result.output
    user = db_session.scalar(select(User).where(User.username == "vuelve"))
    assert user.disabled is False
    assert verify_password("otra-contraseña-larga-456", user.password_hash)


@pytest.mark.spec("RF-R1-10")
def test_create_user_con_contrasena_corta_falla(invoke, db_session) -> None:
    result = invoke(["create-user", "debil"], input="corta\ncorta\n")

    assert result.exit_code != 0
    assert db_session.scalar(select(User).where(User.username == "debil")) is None


@pytest.mark.spec("RF-R1-10")
def test_create_user_con_sesion_real_no_lanza_detached_instance_error() -> None:
    """Regresión: a diferencia de `invoke` (que reutiliza `db_session` sin
    cerrarla), la CLI real usa `app.db.session.get_db`, que hace `commit()`
    y `close()` al salir del comando. Acceder a un atributo del usuario
    devuelto tras cerrar la sesión disparaba `DetachedInstanceError` si se
    leía fuera del `with`; aquí se ejercita la ruta real de principio a fin.
    """
    from app.db.session import SessionLocal

    try:
        result = runner.invoke(
            app,
            ["create-user", "gonzalo-sesion-real"],
            input="una-contraseña-larga-123\nuna-contraseña-larga-123\n",
        )

        assert result.exit_code == 0, result.output
        assert "creado con rol 'lector'" in result.output
    finally:
        cleanup = SessionLocal()
        try:
            user = cleanup.scalar(select(User).where(User.username == "gonzalo-sesion-real"))
            if user is not None:
                cleanup.delete(user)
                cleanup.commit()
        finally:
            cleanup.close()


@pytest.mark.spec("RF-R1-09")
def test_reset_password_genera_temporal_y_fuerza_cambio(invoke, db_session, make_user) -> None:
    user = make_user(username="gonzalo", password="una-contraseña-larga-123")

    result = invoke(["reset-password", "gonzalo"])

    assert result.exit_code == 0, result.output
    db_session.refresh(user)
    assert user.must_change_password is True
    assert not verify_password("una-contraseña-larga-123", user.password_hash)
    assert "reset-password" in _audit_actions(db_session, "gonzalo")
    # La contraseña temporal no debe quedar en el detalle auditado.
    audit_row = db_session.scalar(
        select(AuditLog).where(AuditLog.entity_id == "gonzalo", AuditLog.action == "reset-password")
    )
    assert audit_row.detail is None


@pytest.mark.spec("RF-R1-09")
def test_reset_password_usuario_inexistente_falla(invoke) -> None:
    result = invoke(["reset-password", "fantasma"])

    assert result.exit_code != 0
    assert "fantasma" in result.output


@pytest.mark.spec("RF-R1-11")
def test_unlock_levanta_bloqueo_existente(invoke, db_session) -> None:
    db_session.add(
        AccountLock(
            username="bloqueada",
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
    )
    db_session.flush()

    result = invoke(["unlock", "bloqueada"])

    assert result.exit_code == 0, result.output
    restantes = db_session.scalars(select(AccountLock).where(AccountLock.username == "bloqueada")).all()
    assert restantes == []
    assert "unlock" in _audit_actions(db_session, "bloqueada")


@pytest.mark.spec("RF-R1-11")
def test_unlock_sin_bloqueo_es_idempotente(invoke) -> None:
    result = invoke(["unlock", "nadie-bloqueado"])

    assert result.exit_code == 0
    assert "no tenía" in result.output


@pytest.mark.spec("RF-R1-11")
def test_disable_y_enable_usuario(invoke, db_session, make_user) -> None:
    make_user(username="alterna")

    result_disable = invoke(["disable", "alterna"])
    assert result_disable.exit_code == 0, result_disable.output
    user = db_session.scalar(select(User).where(User.username == "alterna"))
    assert user.disabled is True

    result_enable = invoke(["enable", "alterna"])
    assert result_enable.exit_code == 0, result_enable.output
    db_session.refresh(user)
    assert user.disabled is False

    assert _audit_actions(db_session, "alterna") == ["disable", "enable"]


@pytest.mark.spec("RF-R1-11")
def test_disable_usuario_inexistente_falla(invoke) -> None:
    result = invoke(["disable", "fantasma"])

    assert result.exit_code != 0


@pytest.mark.spec("RF-R1-11")
def test_enable_usuario_inexistente_falla(invoke) -> None:
    result = invoke(["enable", "fantasma"])

    assert result.exit_code != 0


@pytest.mark.spec("RF-R1-11")
def test_sessions_revoke_revoca_todas_las_sesiones_activas(invoke, db_session, make_user) -> None:
    user = make_user(username="con-sesiones")
    activa = SessionModel(
        user_id=user.id,
        token_hash="a" * 64,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        absolute_expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    ya_revocada = SessionModel(
        user_id=user.id,
        token_hash="b" * 64,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        absolute_expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        revoked=True,
    )
    db_session.add_all([activa, ya_revocada])
    db_session.flush()

    result = invoke(["sessions-revoke", "con-sesiones"])

    assert result.exit_code == 0, result.output
    assert "1 sesión" in result.output
    db_session.refresh(activa)
    assert activa.revoked is True
    assert "sessions-revoke" in _audit_actions(db_session, "con-sesiones")


@pytest.mark.spec("RF-R1-11")
def test_sessions_revoke_usuario_inexistente_falla(invoke) -> None:
    result = invoke(["sessions-revoke", "fantasma"])

    assert result.exit_code != 0


@pytest.mark.spec("RF-R1-11")
def test_list_users_muestra_rol_estado_y_bloqueo(invoke, db_session, make_user) -> None:
    make_user(username="activa")
    make_user(username="deshabilitada", disabled=True)
    db_session.add(
        AccountLock(
            username="activa",
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
    )
    db_session.flush()

    result = invoke(["list-users"])

    assert result.exit_code == 0, result.output
    assert "activa" in result.output
    assert "bloqueado hasta" in result.output
    assert "deshabilitado" in result.output


@pytest.mark.spec("RF-R1-11")
def test_list_users_sin_usuarios(invoke) -> None:
    result = invoke(["list-users"])

    assert result.exit_code == 0
    assert "No hay usuarios" in result.output


@pytest.mark.spec("RF-R1-12")
def test_cada_mutacion_registra_auditoria_con_origen_cli(invoke, db_session, make_user) -> None:
    make_user(username="auditada")

    invoke(["disable", "auditada"])

    audit_row = db_session.scalar(
        select(AuditLog).where(AuditLog.entity_id == "auditada", AuditLog.action == "disable")
    )
    assert audit_row is not None
    assert audit_row.actor == "cli"
    assert audit_row.entity == "user"
