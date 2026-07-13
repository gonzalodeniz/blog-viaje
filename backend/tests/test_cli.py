import pytest
from typer.testing import CliRunner

from app.cli.main import app

runner = CliRunner()


@pytest.mark.spec("RNF-R1-07")
def test_cli_version_se_ejecuta() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "bitacora-cli" in result.stdout
