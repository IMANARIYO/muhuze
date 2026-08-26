import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bootstrap import seed_default_accounts
from app.core.config import settings
from app.core.security import verify_password
from app.modules.auth.repository import AccountRepository, AuthorizationRepository


def unique_email() -> str:
    return f"bootstrap-test-{uuid.uuid4().hex}@example.com"


async def test_seeds_configured_super_admin_with_admin_role(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = unique_email()
    monkeypatch.setattr(settings, "super_admin_email", email)
    monkeypatch.setattr(settings, "super_admin_password", "super-secret-password")
    monkeypatch.setattr(settings, "test_seller_email", None)
    monkeypatch.setattr(settings, "test_seller_password", None)

    await seed_default_accounts(db)

    accounts = AccountRepository(db)
    authorization = AuthorizationRepository(db)
    account = await accounts.get_by_email(email)
    assert account is not None
    assert account.is_verified is True
    assert verify_password("super-secret-password", account.password_hash)
    assert await authorization.get_role_names(account.id) == ["admin"]


async def test_seeding_is_idempotent(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = unique_email()
    monkeypatch.setattr(settings, "super_admin_email", email)
    monkeypatch.setattr(settings, "super_admin_password", "super-secret-password")
    monkeypatch.setattr(settings, "test_seller_email", None)
    monkeypatch.setattr(settings, "test_seller_password", None)

    await seed_default_accounts(db)
    await seed_default_accounts(db)

    accounts = AccountRepository(db)
    authorization = AuthorizationRepository(db)
    account = await accounts.get_by_email(email)
    assert account is not None
    # Re-running didn't duplicate the role assignment either.
    assert await authorization.get_role_names(account.id) == ["admin"]


async def test_seeds_test_seller_with_buyer_and_seller_roles_outside_production(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = unique_email()
    monkeypatch.setattr(settings, "super_admin_email", None)
    monkeypatch.setattr(settings, "super_admin_password", None)
    monkeypatch.setattr(settings, "test_seller_email", email)
    monkeypatch.setattr(settings, "test_seller_password", "super-secret-password")
    monkeypatch.setattr(settings, "environment", "development")

    await seed_default_accounts(db)

    accounts = AccountRepository(db)
    authorization = AuthorizationRepository(db)
    account = await accounts.get_by_email(email)
    assert account is not None
    assert sorted(await authorization.get_role_names(account.id)) == ["buyer", "seller"]


async def test_does_not_seed_test_seller_in_production(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = unique_email()
    monkeypatch.setattr(settings, "super_admin_email", None)
    monkeypatch.setattr(settings, "super_admin_password", None)
    monkeypatch.setattr(settings, "test_seller_email", email)
    monkeypatch.setattr(settings, "test_seller_password", "super-secret-password")
    monkeypatch.setattr(settings, "environment", "production")

    await seed_default_accounts(db)

    accounts = AccountRepository(db)
    assert await accounts.get_by_email(email) is None


async def test_does_not_seed_when_env_vars_unset(
    db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "super_admin_email", None)
    monkeypatch.setattr(settings, "super_admin_password", None)
    monkeypatch.setattr(settings, "test_seller_email", None)
    monkeypatch.setattr(settings, "test_seller_password", None)

    # Should not raise, and should not create anything.
    await seed_default_accounts(db)
