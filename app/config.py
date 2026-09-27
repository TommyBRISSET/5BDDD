from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    debug: bool = False
    database_url: str
    api_key: str = "default-key"
    port: int = 8000

    jwt_secret_key: str = "585ed8d85S8D5ds8ds8585S8ZDC8"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Retourne la configuration globale mise en cache."""
    return Settings()