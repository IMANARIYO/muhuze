from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.premium.repository import PremiumPlanRepository
from app.modules.premium.service import seed_default_premium_plans
from app.modules.products.repository import AttributeRepository
from app.modules.products.service import seed_default_attributes
from app.modules.sellers.models import SellerStatus
from app.modules.sellers.repository import SellerRepository

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


async def _ensure_test_seller_profile(
    db: AsyncSession,
    accounts: AccountRepository,
    sellers: SellerRepository,
    *,
    account_email: str,
    admin_email: str | None,
) -> None:
    """Dev convenience: the test-seller account also gets a ready-made
    `active` Seller profile, so it can actually write to the catalog
    (create variants/images) out of the box. Separating the `seller` role
    from an active Seller profile is intentional — this seed just keeps
    the two in sync for the test account on non-production. If a profile
    already exists it is left alone — never silently re-approves a
    suspended/rejected seller."""
    account = await accounts.get_by_email(account_email)
    if account is None:
        logger.warning(
            "Cannot seed seller profile for %s — account does not exist", account_email
        )
        return

    existing = await sellers.get_by_account_id(account.id)
    if existing is not None:
        if existing.status != SellerStatus.ACTIVE:
            logger.warning(
                "Test-seller profile exists but is %s — not auto-approving",
                existing.status,
            )
        return

    admin = (
        await accounts.get_by_email(admin_email) if admin_email is not None else None
    )
    seller = await sellers.create(
        account_id=account.id,
        business_name="Muhuze Test Seller",
        business_description=(
            "Seeded development seller — active profile for testing the "
            "seller catalog flow out of the box."
        ),
    )
    seller.status = SellerStatus.ACTIVE
    seller.reviewed_at = datetime.now(UTC)
    if admin is not None:
        seller.reviewed_by = admin.id
    await db.flush()
    logger.info("Seeded active seller profile for %s", account_email)


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
        await _ensure_test_seller_profile(
            db,
            accounts,
            SellerRepository(db),
            account_email=settings.test_seller_email,
            admin_email=settings.super_admin_email,
        )

    created_plans = await seed_default_premium_plans(PremiumPlanRepository(db))
    if created_plans:
        logger.info("Seeded %s default premium plan(s)", created_plans)

    created_attributes = await seed_default_attributes(AttributeRepository(db))
    if created_attributes:
        logger.info("Seeded %s default attribute(s)", created_attributes)

    await db.commit()
