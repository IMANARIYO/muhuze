import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_service import SellerService
from app.modules.wallets.wallet_exceptions import NotASellerError
from app.modules.wallets.wallet_permissions import WALLET_READ_OWN
from app.modules.wallets.wallet_service import WalletService


def get_wallet_service(session: Annotated[AsyncSession, Depends(get_session)]) -> WalletService:
    return WalletService(session)


async def get_own_seller_id(
    account: Annotated[Account, Depends(require_permission(WALLET_READ_OWN))],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> uuid.UUID:
    """The caller's seller id, in ANY status: a suspended or closed seller
    must still be able to see what they are owed."""
    seller_id = await seller_service.find_seller_id(account.id)
    if seller_id is None:
        raise NotASellerError()
    return seller_id
