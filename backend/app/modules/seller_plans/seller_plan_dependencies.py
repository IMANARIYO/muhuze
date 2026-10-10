from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_service import SellerService


def get_seller_plan_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> SellerPlanService:
    return SellerPlanService(session=session, seller_service=seller_service)
