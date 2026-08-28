from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.premium.controller import PremiumController


def get_premium_controller(db: AsyncSession = Depends(get_db)) -> PremiumController:
    return PremiumController(db)
