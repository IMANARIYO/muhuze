from functools import lru_cache
from typing import Literal, Self
from urllib.parse import parse_qsl, urlencode

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["text", "json"]
JwtAlgorithm = Literal["HS256", "HS384", "HS512"]

ASYNC_POSTGRES_SCHEME = "postgresql+asyncpg://"
JWT_SECRET_MIN_LENGTH = 32


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

    # PostgreSQL. A plain `postgresql://` URL is accepted and run on asyncpg.
    database_url: str

    # Authentication. The access token is a short-lived JWT; the refresh token
    # is opaque and stored hashed (app/modules/auth).
    jwt_secret_key: SecretStr
    jwt_algorithm: JwtAlgorithm = "HS256"
    access_token_expire_minutes: int = Field(default=15, gt=0)
    refresh_token_expire_days: int = Field(default=30, gt=0)
    verification_code_expire_minutes: int = Field(default=10, gt=0)
    verification_code_max_attempts: int = Field(default=5, gt=0)
    password_reset_token_expire_minutes: int = Field(default=30, gt=0)
    # Frontend page that receives `?token=...` from the password reset email.
    password_reset_url: str = "http://localhost:5173/reset-password"

    # Email (app/infrastructure/notifications). Without SMTP_HOST, emails are
    # logged instead of sent — allowed in development and test only.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True

    # An empty value (`LOG_LEVEL=` in .env) means "not set", not an invalid level.
    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        return (value.strip().upper() or None) if isinstance(value, str) else value

    @field_validator("log_format", mode="before")
    @classmethod
    def _normalize_log_format(cls, value: object) -> object:
        return (value.strip().lower() or None) if isinstance(value, str) else value

    @field_validator(
        "smtp_host", "smtp_username", "smtp_password", "smtp_from_email", mode="before"
    )
    @classmethod
    def _empty_means_unset(cls, value: object) -> object:
        return (value.strip() or None) if isinstance(value, str) else value

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg_driver(cls, value: str) -> str:
        value = value.strip()
        for scheme in ("postgresql://", "postgres://"):
            if value.startswith(scheme):
                value = ASYNC_POSTGRES_SCHEME + value.removeprefix(scheme)
                break
        if not value.startswith(ASYNC_POSTGRES_SCHEME):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL (postgresql://...)")
        return _translate_libpq_query(value)

    @field_validator("jwt_secret_key")
    @classmethod
    def _require_long_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < JWT_SECRET_MIN_LENGTH:
            raise ValueError(f"JWT_SECRET_KEY must be at least {JWT_SECRET_MIN_LENGTH} characters")
        return value

    @model_validator(mode="after")
    def _validate_email_delivery(self) -> Self:
        if self.smtp_host is None:
            if self.is_deployed:
                raise ValueError("SMTP_HOST is required in staging and production")
        elif self.email_from_address is None:
            raise ValueError("SMTP_FROM_EMAIL (or SMTP_USERNAME) is required when SMTP_HOST is set")
        return self

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

    @property
    def email_from_address(self) -> str | None:
        return self.smtp_from_email or self.smtp_username


def _translate_libpq_query(database_url: str) -> str:
    """Hosted PostgreSQL providers hand out libpq-style URLs
    (`?sslmode=require&channel_binding=require`). asyncpg names the first
    option `ssl` and has no equivalent of the second, so translate them."""
    base, separator, query = database_url.partition("?")
    if not separator:
        return database_url
    params = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        if key == "channel_binding":
            continue
        params.append(("ssl" if key == "sslmode" else key, value))
    return f"{base}?{urlencode(params)}" if params else base


@lru_cache
def get_settings() -> Settings:
    return Settings()
