import os
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./consciousness.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Application settings
    APP_NAME: str = "House Consciousness System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000


# Global settings instance
settings = Settings()
