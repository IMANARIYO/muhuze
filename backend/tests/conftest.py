import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.main import app


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
