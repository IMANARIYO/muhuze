from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MUHUZE Global Link"
    environment: str = "development"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    otp_expire_minutes: int = 10
    password_reset_token_expire_minutes: int = 30

    # Bootstrapped at startup — see app/core/bootstrap.py. Unset means "don't
    # seed this account". super_admin_* applies in every environment (an
    # admin must exist somewhere); test_seller_* is skipped outright in
    # production regardless of whether it's set.
    super_admin_email: str | None = None
    super_admin_password: str | None = None
    test_seller_email: str | None = None
    test_seller_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
