from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.orders.order_service import OrderService
from app.modules.products.product_dependencies import get_product_service
from app.modules.products.product_service import ProductService
from app.modules.seller_plans.seller_plan_dependencies import get_seller_plan_service
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_service import SellerService
from app.modules.wallets.wallet_dependencies import get_wallet_service
from app.modules.wallets.wallet_service import WalletService


def get_order_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
    seller_plan_service: Annotated[SellerPlanService, Depends(get_seller_plan_service)],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
    wallet_service: Annotated[WalletService, Depends(get_wallet_service)],
) -> OrderService:
    return OrderService(
        session=session,
        product_service=product_service,
        seller_plan_service=seller_plan_service,
        seller_service=seller_service,
        wallet_service=wallet_service,
    )
