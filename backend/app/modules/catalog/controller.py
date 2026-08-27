import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.repository import CatalogRepository
from app.modules.catalog.schemas import (
    CatalogFilters,
    CatalogListingItem,
    CatalogProductDetail,
)
from app.modules.catalog.service import CatalogService


class CatalogController:
    """Translates HTTP requests to the buyer-facing catalog service.
    Read-only and public — the entry points a storefront calls."""

    def __init__(self, db: AsyncSession) -> None:
        self.catalog = CatalogService(CatalogRepository(db))

    async def search_active_listings(
        self,
        *,
        category_id: uuid.UUID | None,
        brand_id: uuid.UUID | None,
        search: str | None,
        sort: str | None,
        min_price: float | None,
        max_price: float | None,
        conditions: list | None,
        in_stock: bool,
        filters: dict | None,
    ) -> list[CatalogListingItem]:
        return await self.catalog.search_active_listings(
            category_id=category_id,
            brand_id=brand_id,
            search=search,
            sort=sort,
            min_price=min_price,
            max_price=max_price,
            conditions=conditions,
            in_stock=in_stock,
            filters=filters,
        )

    async def get_filters(self, category_id: uuid.UUID | None) -> CatalogFilters:
        return await self.catalog.get_filters(category_id)

    async def get_product_detail(
        self, product_id: uuid.UUID
    ) -> CatalogProductDetail:
        return await self.catalog.get_product_detail(product_id)
