from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.orders.order_dependencies import get_order_service
from app.modules.orders.order_service import OrderService
from app.modules.payments.payment_service import PaymentService


def get_payment_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    order_service: Annotated[OrderService, Depends(get_order_service)],
) -> PaymentService:
    return PaymentService(session=session, order_service=order_service)
