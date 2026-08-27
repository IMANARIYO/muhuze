from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.products.controller import (
    AttributeController,
    BrandController,
    ListingController,
    ProductController,
)


def get_brand_controller(db: AsyncSession = Depends(get_db)) -> BrandController:
    return BrandController(db)


def get_attribute_controller(db: AsyncSession = Depends(get_db)) -> AttributeController:
    return AttributeController(db)


def get_product_controller(db: AsyncSession = Depends(get_db)) -> ProductController:
    return ProductController(db)


def get_listing_controller(db: AsyncSession = Depends(get_db)) -> ListingController:
    return ListingController(db)
