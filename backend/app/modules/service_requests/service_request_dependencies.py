from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.orders.order_dependencies import get_order_service
from app.modules.orders.order_service import OrderService
from app.modules.products.product_dependencies import get_product_service
from app.modules.products.product_service import ProductService
from app.modules.sellers.seller_dependencies import get_seller_service
from app.modules.sellers.seller_service import SellerService
from app.modules.service_requests.service_request_service import ServiceRequestService


def get_service_request_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> ServiceRequestService:
    return ServiceRequestService(
        session=session,
        product_service=product_service,
        order_service=order_service,
        seller_service=seller_service,
    )
