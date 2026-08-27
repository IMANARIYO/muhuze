import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.repository import CatalogRepository
from app.modules.catalog.schemas import (
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
    ) -> list[CatalogListingItem]:
        return await self.catalog.search_active_listings(
            category_id=category_id, brand_id=brand_id, search=search, sort=sort
        )

    async def get_product_detail(
        self, product_id: uuid.UUID
    ) -> CatalogProductDetail:
        return await self.catalog.get_product_detail(product_id)
