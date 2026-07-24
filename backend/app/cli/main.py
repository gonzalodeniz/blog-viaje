"""Implementa: RF-R1-08, RF-R1-09, RF-R1-10, RF-R1-11, RF-R1-12.

`bitacora-cli`: comandos de rescate ejecutables solo desde una shell del
servidor (`docker compose exec backend bitacora-cli <cmd>`), nunca por
HTTP (RF-R1-08 se cumple por construcción: no hay ninguna ruta que exponga
este módulo). La lógica vive en `app.services.rescue_cli`; aquí solo se
adapta esa lógica a entrada/salida de terminal.
"""

from contextlib import contextmanager
from typing import Iterator

import typer
from sqlalchemy.orm import Session as DbSession

from app.db.session import get_db
from app.services import rescue_cli

app = typer.Typer(
    help="CLI de rescate de Bitácora — ejecutar solo desde el servidor.",
    no_args_is_help=True,
)

_db_session = contextmanager(get_db)


@contextmanager
def _session() -> Iterator[DbSession]:
    with _db_session() as db:
        yield db


@app.command()
def version() -> None:
    """Muestra la versión de la CLI."""
    typer.echo("bitacora-cli 0.1.0")


@app.command("create-user")
def create_user(
    username: str,
    admin: bool = typer.Option(False, "--admin", help="Crea/rehabilita el usuario con rol admin."),
) -> None:
    """Alta o rehabilitación de un usuario con contraseña interactiva (RF-R1-10)."""
    password = typer.prompt("Contraseña", hide_input=True, confirmation_prompt=True)
    with _session() as db:
        try:
            result = rescue_cli.create_or_reenable_user(db, username, password, admin=admin)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        # Se lee dentro del `with`: fuera de él la sesión ya se ha cerrado
        # (commit + close en app.db.session.get_db) y el objeto queda
        # "detached" — acceder a un atributo lanzaría DetachedInstanceError.
        accion = "creado" if result.created else "rehabilitado"
        role = result.user.role

    typer.echo(f"Usuario '{username}' {accion} con rol '{role}'.")


@app.command("reset-password")
def reset_password(username: str) -> None:
    """Genera una contraseña temporal y fuerza cambio en el siguiente login (RF-R1-09)."""
    with _session() as db:
        try:
            temporary_password = rescue_cli.reset_password(db, username)
        except rescue_cli.UserNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

    typer.echo(f"Contraseña temporal para '{username}' (se muestra una única vez):")
    typer.echo(temporary_password)
    typer.echo("El usuario deberá cambiarla en el próximo login.")


@app.command()
def unlock(username: str) -> None:
    """Levanta cualquier bloqueo temporal activo del usuario (RF-R1-11)."""
    with _session() as db:
        habia_bloqueo = rescue_cli.unlock_user(db, username)

    if habia_bloqueo:
        typer.echo(f"Bloqueo levantado para '{username}'.")
    else:
        typer.echo(f"'{username}' no tenía ningún bloqueo activo.")


@app.command()
def disable(username: str) -> None:
    """Deshabilita un usuario (RF-R1-11)."""
    with _session() as db:
        try:
            rescue_cli.disable_user(db, username)
        except rescue_cli.UserNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

    typer.echo(f"Usuario '{username}' deshabilitado.")


@app.command()
def enable(username: str) -> None:
    """Rehabilita un usuario deshabilitado (RF-R1-11)."""
    with _session() as db:
        try:
            rescue_cli.enable_user(db, username)
        except rescue_cli.UserNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

    typer.echo(f"Usuario '{username}' habilitado.")


@app.command("sessions-revoke")
def sessions_revoke(username: str) -> None:
    """Revoca todas las sesiones activas de un usuario (RF-R1-11)."""
    with _session() as db:
        try:
            revocadas = rescue_cli.revoke_sessions(db, username)
        except rescue_cli.UserNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

    typer.echo(f"{revocadas} sesión(es) revocada(s) para '{username}'.")


@app.command("list-users")
def list_users() -> None:
    """Lista los usuarios con rol, estado y bloqueo activo (RF-R1-11)."""
    with _session() as db:
        rows = rescue_cli.list_users(db)

    if not rows:
        typer.echo("No hay usuarios.")
        return

    for row in rows:
        estado = "deshabilitado" if row.disabled else "activo"
        bloqueo = f"bloqueado hasta {row.locked_until.isoformat()}" if row.locked_until else "sin bloqueo"
        ultimo_acceso = row.last_login_at.isoformat() if row.last_login_at else "nunca"
        typer.echo(f"{row.username}\trol={row.role}\t{estado}\t{bloqueo}\tultimo_acceso={ultimo_acceso}")


if __name__ == "__main__":
    app()
