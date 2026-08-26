from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.sellers.controller import SellerController


def get_seller_controller(db: AsyncSession = Depends(get_db)) -> SellerController:
    return SellerController(db)
