import pytest
from pydantic import ValidationError


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:pass@localhost:5432/muhuze",
        "postgres://user:pass@localhost:5432/muhuze",
        "postgresql+asyncpg://user:pass@localhost:5432/muhuze",
    ],
)
def test_database_url_always_uses_asyncpg(make_settings, url: str) -> None:
    settings = make_settings(database_url=url)
    assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/muhuze"


def test_libpq_ssl_options_are_translated_for_asyncpg(make_settings) -> None:
    settings = make_settings(
        database_url="postgresql://user:pass@db.example.test/muhuze?sslmode=require&channel_binding=require"
    )
    assert (
        settings.database_url == "postgresql+asyncpg://user:pass@db.example.test/muhuze?ssl=require"
    )


def test_non_postgres_database_url_is_rejected(make_settings) -> None:
    with pytest.raises(ValidationError):
        make_settings(database_url="sqlite:///local.db")


def test_short_jwt_secret_is_rejected(make_settings) -> None:
    with pytest.raises(ValidationError):
        make_settings(jwt_secret_key="too-short")


def test_jwt_secret_is_not_shown_in_repr(make_settings) -> None:
    secret = "a-secret-that-must-never-appear-in-logs"
    assert secret not in repr(make_settings(jwt_secret_key=secret))


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_environments_require_smtp(make_settings, environment: str) -> None:
    with pytest.raises(ValidationError):
        make_settings(environment=environment, smtp_host=None)


def test_smtp_host_needs_a_from_address(make_settings) -> None:
    with pytest.raises(ValidationError):
        make_settings(smtp_host="smtp.example.test")
    settings = make_settings(smtp_host="smtp.example.test", smtp_username="mailer@example.test")
    assert settings.email_from_address == "mailer@example.test"


def test_empty_smtp_values_mean_unset(make_settings) -> None:
    settings = make_settings(smtp_host="", smtp_username=" ", smtp_password="")
    assert settings.smtp_host is None
    assert settings.smtp_username is None
    assert settings.smtp_password is None
