import pytest

from app.core.config import Settings


@pytest.mark.spec("RNF-R1-07")
def test_database_url_se_construye_desde_los_ajustes() -> None:
    settings = Settings(
        postgres_user="u", postgres_password="p", postgres_host="h", postgres_port=5432, postgres_db="d"
    )

    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/d"
