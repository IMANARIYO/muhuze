from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.revenue.controller import RevenueController


def get_revenue_controller(db: AsyncSession = Depends(get_db)) -> RevenueController:
    return RevenueController(db)
