import asyncio
import os
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config.settings import Settings
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Used when a test never touches the database: the engine connects lazily,
# so this address is never dialled.
UNUSED_DATABASE_URL = "postgresql+asyncpg://unused:unused@localhost:1/unused_test"
TEST_JWT_SECRET = "test-only-jwt-secret-not-used-anywhere-else"  # noqa: S105
TEST_DATABASE_SUFFIX = "_test"

SettingsFactory = Callable[..., Settings]


@pytest.fixture(scope="session")
def test_database_url() -> str | None:
    """TEST_DATABASE_URL from the environment, or from backend/.env."""
    return (
        os.environ.get("TEST_DATABASE_URL")
        or dotenv_values(BACKEND_DIR / ".env").get("TEST_DATABASE_URL")
        or None
    )


@pytest.fixture
def make_settings(test_database_url: str | None) -> SettingsFactory:
    """Build Settings for a test. Apart from the test database URL, nothing
    comes from a developer's local .env."""

    def _make_settings(**overrides: object) -> Settings:
        values: dict[str, object] = {
            "environment": "test",
            "database_url": test_database_url or UNUSED_DATABASE_URL,
            "jwt_secret_key": TEST_JWT_SECRET,
        }
        values.update(overrides)
        if values["environment"] in ("staging", "production"):
            # Deployed environments refuse to start without SMTP.
            values.setdefault("smtp_host", "smtp.example.test")
            values.setdefault("smtp_from_email", "no-reply@example.test")
        return Settings(**values, _env_file=None)

    return _make_settings


@pytest.fixture
def settings(make_settings: SettingsFactory) -> Settings:
    return make_settings()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Database-backed tests ────────────────────────────────────────────────
#
# These run against a real PostgreSQL database (TEST_DATABASE_URL). The
# schema is rebuilt once per run by the Alembic migrations, so the migrations
# are tested too. Each test runs inside a transaction that is rolled back, so
# tests never see each other's rows.


async def _reset_schema(database_url: str) -> None:
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


@pytest.fixture(scope="session")
def migrated_database_url(test_database_url: str | None) -> str:
    if not test_database_url:
        pytest.fail(
            "This test needs PostgreSQL. Set TEST_DATABASE_URL (environment or backend/.env) "
            f"to a database whose name ends with '{TEST_DATABASE_SUFFIX}'."
        )
    database_url = Settings(
        environment="test",
        database_url=test_database_url,
        jwt_secret_key=TEST_JWT_SECRET,
        _env_file=None,
    ).database_url
    database_name = make_url(database_url).database or ""
    if not database_name.endswith(TEST_DATABASE_SUFFIX):
        # The schema is dropped below; never do that to a non-test database.
        pytest.fail(
            f"Refusing to run tests against database '{database_name}': "
            f"its name must end with '{TEST_DATABASE_SUFFIX}'."
        )

    asyncio.run(_reset_schema(database_url))
    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    alembic_config.attributes["database_url"] = database_url
    alembic_config.attributes["configure_logger"] = False
    command.upgrade(alembic_config, "head")
    return database_url


@pytest.fixture
async def db_connection(migrated_database_url: str) -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(migrated_database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def session_factory(db_connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    """Sessions that all share the test's connection. A service's `commit()`
    only releases a savepoint, so the outer transaction can still roll
    everything back when the test ends."""
    return async_sessionmaker(
        bind=db_connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )


class RecordingEmailSender:
    """Stands in for the real email sender and keeps what would have been sent."""

    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


@pytest.fixture
def email_outbox() -> RecordingEmailSender:
    return RecordingEmailSender()


@pytest.fixture
async def db_client(
    app: FastAPI,
    session_factory: async_sessionmaker[AsyncSession],
    email_outbox: RecordingEmailSender,
) -> AsyncIterator[AsyncClient]:
    """An API client whose app uses the test transaction and records emails."""
    app.state.session_factory = session_factory
    app.state.email_sender = email_outbox
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
