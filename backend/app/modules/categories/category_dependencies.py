from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.categories.category_service import CategoryService


def get_category_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryService:
    return CategoryService(session)
