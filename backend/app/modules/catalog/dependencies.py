from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.catalog.controller import CatalogController


def get_catalog_controller(db: AsyncSession = Depends(get_db)) -> CatalogController:
    return CatalogController(db)
