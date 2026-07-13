"""Configuración de la aplicación leída desde variables de entorno (.env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_db: str = "bitacora"
    postgres_user: str = "bitacora"
    postgres_password: str = "bitacora"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    secret_key: str = "change-me-in-.env"
    session_ttl_hours: int = 24
    session_remember_days: int = 30
    session_absolute_max_days: int = 90
    login_attempts_retention_days: int = 90

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
