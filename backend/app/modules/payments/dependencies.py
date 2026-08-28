from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.payments.controller import PaymentController


def get_payment_controller(db: AsyncSession = Depends(get_db)) -> PaymentController:
    return PaymentController(db)
