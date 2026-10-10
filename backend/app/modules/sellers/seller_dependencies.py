from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.auth_dependencies import get_current_account
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_service import AuthorizationService
from app.modules.sellers.seller_model import Seller
from app.modules.sellers.seller_service import SellerService


def get_seller_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> SellerService:
    return SellerService(
        session=session,
        authorization=AuthorizationService(session),
        file_storage=request.app.state.file_storage,
    )


async def get_current_active_seller(
    account: Annotated[Account, Depends(get_current_account)],
    service: Annotated[SellerService, Depends(get_seller_service)],
) -> Seller:
    """The caller's seller, if it may trade right now; 403 otherwise.

    Other features put this on every endpoint that only an approved, active
    seller may use (after their own `require_permission`).
    """
    return await service.get_active_seller(account.id)
