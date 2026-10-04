from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["text", "json"]


class Settings(BaseSettings):
    """Application settings, read from environment variables and `.env`.

    Only infrastructure/runtime configuration lives here. Business parameters
    that affect money (commission rates, plans, payment destinations) are
    admin-managed data owned by their modules, never settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "MUHUZE Global Link"
    environment: Environment = "development"

    # Unset means "derive from environment" — see effective_log_level/format.
    log_level: LogLevel | None = None
    log_format: LogFormat | None = None

    # An empty value (`LOG_LEVEL=` in .env) means "not set", not an invalid level.
    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        return (value.strip().upper() or None) if isinstance(value, str) else value

    @field_validator("log_format", mode="before")
    @classmethod
    def _normalize_log_format(cls, value: object) -> object:
        return (value.strip().lower() or None) if isinstance(value, str) else value

    @property
    def is_deployed(self) -> bool:
        """Staging and production: machine-read logs, no development defaults."""
        return self.environment in ("staging", "production")

    @property
    def effective_log_level(self) -> LogLevel:
        if self.log_level is not None:
            return self.log_level
        return "DEBUG" if self.environment == "development" else "INFO"

    @property
    def effective_log_format(self) -> LogFormat:
        if self.log_format is not None:
            return self.log_format
        return "json" if self.is_deployed else "text"


@lru_cache
def get_settings() -> Settings:
    return Settings()
