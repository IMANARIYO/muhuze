import os

# Must run before any `app.*` import — app.core.config.settings is built at
# import time. Two overrides:
#
# DATABASE_URL: in-memory SQLite instead of the real Postgres DB in .env —
# no live DB needed to run tests, and no Alembic migration history to
# replay (one of our migrations uses plain ALTER TABLE on a FK constraint,
# which SQLite can't do outside of Alembic's batch mode) — the schema is
# built directly from the current ORM models instead, once per test
# session, in _test_database below.
#
# ENVIRONMENT=test: makes app.core.security use a low-cost Argon2 config.
# Argon2's slowness is the security point in dev/production; in tests it's
# pure overhead (~160ms/hash) that dominates the suite's runtime far more
# than the database does.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.db.models
from app.core.database import AsyncSessionLocal, Base, engine
from app.main import app
from app.modules.auth.models import Role

# Mirrors the DEFAULT_ROLES seeded by the
# 8f020f9eafd8_add_verification_password_reset_and_ migration — that
# migration is a frozen historical record and shouldn't import live app
# code, so this is deliberately a separate, small re-declaration for the
# in-memory test DB rather than a shared import.
_DEFAULT_ROLES = [
    {"name": "buyer", "description": "Can browse and purchase products."},
    {"name": "seller", "description": "Can list and sell products."},
    {"name": "admin", "description": "Platform administrator."},
]


@pytest.fixture(scope="session", autouse=True)
async def _test_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        session.add_all(Role(**role) for role in _DEFAULT_ROLES)
        await session.commit()

    yield
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def captured_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Intercepts app.core.notifications.send_email so tests can assert on
    OTP codes / reset tokens without a real email provider."""
    sent: list[dict] = []

    def fake_send_email(*, to: str, subject: str, body: str) -> None:
        sent.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr("app.core.notifications.send_email", fake_send_email)
    return sent
