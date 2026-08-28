import uuid
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_account
from app.modules.auth.exceptions import InsufficientPermissionsError
from app.modules.auth.models import Account
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.auth.service import AuthorizationService
from app.modules.products.controller import (
    AttributeController,
    BrandController,
    ListingController,
    ProductController,
)
from app.modules.sellers.models import SellerStatus
from app.modules.sellers.repository import SellerRepository


def get_brand_controller(db: AsyncSession = Depends(get_db)) -> BrandController:
    return BrandController(db)


def get_attribute_controller(db: AsyncSession = Depends(get_db)) -> AttributeController:
    return AttributeController(db)


def get_product_controller(db: AsyncSession = Depends(get_db)) -> ProductController:
    return ProductController(db)


def get_listing_controller(db: AsyncSession = Depends(get_db)) -> ListingController:
    return ListingController(db)


def get_authorization_service(db: AsyncSession = Depends(get_db)) -> AuthorizationService:
    return AuthorizationService(AuthorizationRepository(db), AccountRepository(db))


@dataclass(frozen=True, slots=True)
class ProductActor:
    """Who is writing to the catalog right now. `seller_id=None` means
    admin — unrestricted, matches every pre-existing admin-only call
    site's behavior exactly. A non-None `seller_id` means an active
    seller — ProductService/ProductVariantService/ProductImageService use
    it to gate ownership while a product is still
    draft/pending_review/rejected, and to identify the requester once
    it's active (any active seller may extend it further)."""

    account: Account
    seller_id: uuid.UUID | None


async def require_admin_or_active_seller(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
) -> ProductActor:
    """Dependency for the catalog-write endpoints that both admins and
    sellers may call (create/update/submit a product, create/update a
    variant, upload/delete an image). Admin wins if the account holds
    both roles — matches the "admin can do anything" behavior every
    other module already has. Raises InsufficientPermissionsError (403)
    if the account is neither an admin nor a currently-active seller."""
    authorization = AuthorizationService(
        AuthorizationRepository(db), AccountRepository(db)
    )
    if await authorization.has_role(account.id, "admin"):
        return ProductActor(account=account, seller_id=None)

    seller = await SellerRepository(db).get_by_account_id(account.id)
    if seller is not None and seller.status == SellerStatus.ACTIVE:
        return ProductActor(account=account, seller_id=seller.id)

    raise InsufficientPermissionsError()
