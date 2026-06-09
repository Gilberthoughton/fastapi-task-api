"""Application configuration.

Settings are read from environment variables (and a local `.env` file in
development) via pydantic-settings. This keeps secrets and environment-specific
values out of the source tree and makes the app twelve-factor friendly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Any field without a default must be supplied via the environment, so the
    app fails fast on startup if a required value (e.g. SECRET_KEY) is missing.
    """

    # Application
    PROJECT_NAME: str = "Task Management API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # CORS — explicit allow-list of browser origins permitted to call the API.
    # Stored as a comma-separated string and exposed as a list via
    # `cors_origins`. Keeping the raw type as `str` avoids pydantic-settings'
    # automatic JSON decoding of list-typed env vars.
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite:///./tasks.db"

    @property
    def cors_origins(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Caching avoids re-reading the environment on every access and gives the
    whole process a single, consistent configuration object.
    """
    return Settings()


settings = get_settings()
