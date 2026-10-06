"""Helpers shared by the API tests: logged-in accounts with chosen roles."""

import re
import uuid
from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient

from app.core.permission_registry import ALL_PERMISSIONS
from app.modules.authorization.authorization_service import AuthorizationService

API = "/api/v1"
PASSWORD = "correct-horse-battery"


class Actor:
    """A logged-in account: its id and the headers that authenticate it."""

    def __init__(self, account_id: str, access_token: str) -> None:
        self.id = account_id
        self.headers = {"Authorization": f"Bearer {access_token}"}


SignUp = Callable[..., Awaitable[Actor]]


@pytest.fixture
async def synced_permissions(session_factory) -> None:
    """What the application does at startup: load the permission catalog."""
    async with session_factory() as session:
        await AuthorizationService(session).sync_permissions(ALL_PERMISSIONS)


@pytest.fixture
def sign_up(
    db_client: AsyncClient, email_outbox, session_factory, synced_permissions: None
) -> SignUp:
    """Register, verify, and log in an account; optionally give it system roles."""

    async def _sign_up(email: str, *roles: str) -> Actor:
        payload = {"email": email, "password": PASSWORD, "full_name": "Test Person"}
        created = await db_client.post(f"{API}/auth/register", json=payload)
        assert created.status_code == 201, created.text
        body = [m for m in email_outbox.sent if m["to"] == email][-1]["body"]
        code = re.search(r"\b(\d{6})\b", body).group(1)
        confirmed = await db_client.post(
            f"{API}/auth/email/verification/confirm", json={"email": email, "code": code}
        )
        assert confirmed.status_code == 200, confirmed.text

        account_id = created.json()["data"]["id"]
        async with session_factory() as session:
            service = AuthorizationService(session)
            for role in roles:
                await service.assign_role(account_id=uuid.UUID(account_id), role_name=role)
            await session.commit()

        logged_in = await db_client.post(
            f"{API}/auth/login", json={"email": email, "password": PASSWORD}
        )
        assert logged_in.status_code == 200, logged_in.text
        return Actor(account_id, logged_in.json()["data"]["access_token"])

    return _sign_up


@pytest.fixture
async def admin(sign_up: SignUp) -> Actor:
    return await sign_up("admin@example.com", "admin")


@pytest.fixture
async def user(sign_up: SignUp) -> Actor:
    return await sign_up("user@example.com")


JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20


@pytest.fixture
def open_shop(db_client: AsyncClient, admin: Actor):
    """Take an account through the whole application so it becomes an
    approved, active seller. Returns the seller id."""

    async def _open_shop(actor: Actor, business_name: str) -> str:
        application = {
            "business_name": business_name,
            "business_phone": "+250788123456",
            "identity_document_type": "passport",
            "identity_document_number": "PC1234567",
            "location": {"province": "Kigali", "district": "Gasabo", "sector": "Remera"},
        }
        created = await db_client.post(f"{API}/sellers/me", json=application, headers=actor.headers)
        assert created.status_code == 201, created.text
        seller_id = created.json()["data"]["id"]
        uploaded = await db_client.put(
            f"{API}/sellers/me/documents/identity_front",
            files={"file": ("passport.jpg", JPEG)},
            headers=actor.headers,
        )
        assert uploaded.status_code == 200, uploaded.text
        submitted = await db_client.post(f"{API}/sellers/me/submit", headers=actor.headers)
        assert submitted.status_code == 200, submitted.text
        approved = await db_client.post(f"{API}/sellers/{seller_id}/approve", headers=admin.headers)
        assert approved.status_code == 200, approved.text
        return seller_id

    return _open_shop
