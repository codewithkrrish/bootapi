"""Settings for bootapi.

Everything the app needs to know lives here and comes from the environment,
so the same code runs locally, in tests and in Docker without edits.

Copy `.env.example` to `.env` and change the secret before you deploy
anywhere real — the default secret is only there so the template works
out of the box on your own machine.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration, read from the environment (prefix ``BOOTAPI_``)."""

    model_config = SettingsConfigDict(env_prefix="BOOTAPI_", env_file=".env")

    app_name: str = "bootapi"
    app_version: str = "0.1.0"
    debug: bool = False

    # Path to the SQLite file. Point it at :memory: in tests, a volume in Docker.
    database_path: str = "bootapi.db"

    # JWT signing. HS256 is fine for a starter; swap in RS256 when you have
    # more than one service verifying tokens.
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings (built once, reused everywhere)."""
    return Settings()
