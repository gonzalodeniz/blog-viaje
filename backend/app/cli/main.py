"""Esqueleto de bitacora-cli. Los comandos de rescate (RF-R1-08..12) llegan en WP-R1-3."""

import typer

app = typer.Typer(
    help="CLI de rescate de Bitácora — ejecutar solo desde el servidor.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Muestra la versión de la CLI."""
    typer.echo("bitacora-cli 0.1.0")


# Comando ancla: evita que Typer/Click colapse la app en un único comando sin
# nombre mientras "version" es el único registrado (WP-R1-3 añadirá el resto:
# reset-password, create-user, unlock, ...).
@app.command(hidden=True)
def _placeholder() -> None:  # pragma: no cover
    """No usar: reserva la estructura de subcomandos hasta WP-R1-3."""


if __name__ == "__main__":
    app()
