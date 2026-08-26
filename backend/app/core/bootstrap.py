from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.modules.auth.repository import AccountRepository, AuthorizationRepository

logger = get_logger(__name__)


async def _seed_account(
    accounts: AccountRepository,
    authorization: AuthorizationRepository,
    *,
    email: str,
    password: str,
    role_names: list[str],
    label: str,
) -> None:
    if await accounts.get_by_email(email) is not None:
        logger.info("%s account already exists (%s) — skipping seed", label, email)
        return

    account = await accounts.create(
        email=email, phone=None, password_hash=hash_password(password)
    )
    await accounts.mark_verified(account)

    for role_name in role_names:
        role = await authorization.get_role_by_name(role_name)
        if role is None:
            logger.warning(
                "Cannot assign role %r to seeded %s account — role not found in DB",
                role_name,
                label,
            )
            continue
        await authorization.assign_role(account_id=account.id, role_id=role.id)

    logger.info("Seeded %s account: %s (roles: %s)", label, email, role_names)


async def seed_default_accounts(db: AsyncSession) -> None:
    """Idempotent: creates the configured super-admin (and, outside
    production, test-seller) accounts if they don't already exist by email.
    Never overwrites an existing account's password — only fills in what's
    missing. Unset env vars mean "don't seed this account", not an error.
    Called once at app startup — see app/main.py's lifespan.
    """
    accounts = AccountRepository(db)
    authorization = AuthorizationRepository(db)

    if settings.super_admin_email and settings.super_admin_password:
        await _seed_account(
            accounts,
            authorization,
            email=settings.super_admin_email,
            password=settings.super_admin_password,
            role_names=["admin"],
            label="super-admin",
        )

    if (
        settings.test_seller_email
        and settings.test_seller_password
        and settings.environment != "production"
    ):
        await _seed_account(
            accounts,
            authorization,
            email=settings.test_seller_email,
            password=settings.test_seller_password,
            role_names=["buyer", "seller"],
            label="test-seller",
        )

    await db.commit()
