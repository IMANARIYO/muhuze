from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.categories.controller import CategoryController


def get_category_controller(db: AsyncSession = Depends(get_db)) -> CategoryController:
    return CategoryController(db)
