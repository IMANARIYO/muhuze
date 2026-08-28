from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.carts.controller import CartController


def get_cart_controller(db: AsyncSession = Depends(get_db)) -> CartController:
    return CartController(db)
