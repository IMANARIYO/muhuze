from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_account
from app.modules.auth.models import Account
from app.modules.sellers.controller import SellerController
from app.modules.sellers.exceptions import SellerNotActiveError, SellerNotFoundError
from app.modules.sellers.models import Seller, SellerStatus
from app.modules.sellers.repository import SellerRepository


def get_seller_controller(db: AsyncSession = Depends(get_db)) -> SellerController:
    return SellerController(db)


async def get_current_seller(
    account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
) -> Seller:
    """Dependency factory for other modules:
    `Depends(get_current_seller)`. Resolves the caller's own Seller row
    and requires it to be `active` — raises SellerNotFoundError (404) if
    the account never registered as a seller, or SellerNotActiveError
    (409) if it did but isn't currently active. Used anywhere a seller
    action (creating a listing, requesting a product) needs to be gated
    on more than just "is authenticated"."""
    seller = await SellerRepository(db).get_by_account_id(account.id)
    if seller is None:
        raise SellerNotFoundError()
    if seller.status != SellerStatus.ACTIVE:
        raise SellerNotActiveError()
    return seller
