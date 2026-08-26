from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.users.controller import ProfileController


def get_profile_controller(db: AsyncSession = Depends(get_db)) -> ProfileController:
    return ProfileController(db)
