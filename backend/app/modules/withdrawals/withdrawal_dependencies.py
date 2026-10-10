import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_service import SellerService
from app.modules.withdrawals.withdrawal_exceptions import NotASellerError
from app.modules.withdrawals.withdrawal_permissions import (
    PAYOUT_DESTINATION_MANAGE,
    WITHDRAWAL_REQUEST,
)
from app.modules.withdrawals.withdrawal_service import WithdrawalService


def get_withdrawal_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WithdrawalService:
    return WithdrawalService(session)


async def _own_seller_id(account: Account, seller_service: SellerService) -> uuid.UUID:
    seller_id = await seller_service.find_seller_id(account.id)
    if seller_id is None:
        raise NotASellerError()
    return seller_id


async def get_own_seller_id(
    account: Annotated[Account, Depends(require_permission(WITHDRAWAL_REQUEST))],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> uuid.UUID:
    """The caller's seller id, in ANY status: seeing your own withdrawals and
    cancelling a pending one stays possible while suspended. REQUESTING a new
    one goes through `get_current_active_seller` instead."""
    return await _own_seller_id(account, seller_service)


async def get_destination_seller_id(
    account: Annotated[Account, Depends(require_permission(PAYOUT_DESTINATION_MANAGE))],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> uuid.UUID:
    """The caller's seller id for payout destinations, in any status."""
    return await _own_seller_id(account, seller_service)
