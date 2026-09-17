from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application chargée depuis les variables d'environnement ou le fichier .env."""

    app_name: str = "FastAPI App"
    debug: bool = False
    database_url: str
    api_key: str
    port: int = 8000

    # Indique à Pydantic de lire le fichier .env à la racine
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Mise en cache pour éviter de relire le disque à chaque appel
@lru_cache
def get_settings() -> Settings:
    return Settings()