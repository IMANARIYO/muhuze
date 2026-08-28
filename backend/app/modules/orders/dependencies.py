from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.orders.controller import OrderController
from app.modules.orders.fulfillment_controller import FulfillmentController


def get_order_controller(db: AsyncSession = Depends(get_db)) -> OrderController:
    return OrderController(db)


def get_fulfillment_controller(
    db: AsyncSession = Depends(get_db),
) -> FulfillmentController:
    return FulfillmentController(db)
