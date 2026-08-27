import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import (
    Brand,
    Product,
    ProductImage,
    ProductVariant,
    SellerListing,
    VariantAttributeValue,
)
from app.modules.products.repository import (
    ProductRepository,
    ProductVariantRepository,
)
from app.modules.sellers.models import Seller

_ACTIVE = "active"


class CatalogRepository:
    """Read-only data access for the buyer-facing catalog. Assembles the
    denormalized view the frontend needs (active listings joined with
    their product, variant, and seller) using batched queries rather than
    ORM `relationship()` eager-loading — consistent with the rest of the
    codebase."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.variants = ProductVariantRepository(db)

    # --- active listing search ------------------------------------------

    async def list_active_listings(
        self,
        *,
        category_id: uuid.UUID | None,
        brand_id: uuid.UUID | None,
        search: str | None,
        sort: str | None,
    ) -> list[SellerListing]:
        query = select(SellerListing).where(SellerListing.status == _ACTIVE)
        if brand_id is not None or category_id is not None or search is not None:
            product_query = select(Product.id)
            if category_id is not None:
                product_query = product_query.where(Product.category_id == category_id)
            if brand_id is not None:
                product_query = product_query.where(Product.brand_id == brand_id)
            if search is not None:
                product_query = product_query.where(
                    Product.name.ilike(f"%{search}%")
                )
            product_ids = list(
                (await self.db.execute(product_query)).scalars().all()
            )
            if not product_ids:
                return []
            variant_ids = list(
                (
                    await self.db.execute(
                        select(ProductVariant.id).where(
                            ProductVariant.product_id.in_(product_ids),
                            ProductVariant.status == _ACTIVE,
                        )
                    )
                ).scalars().all()
            )
            if not variant_ids:
                return []
            query = query.where(SellerListing.variant_id.in_(variant_ids))

        if sort == "price_desc":
            query = query.order_by(SellerListing.price.desc(), SellerListing.created_at.desc())
        else:
            query = query.order_by(SellerListing.price.asc(), SellerListing.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_product_detail(self, product_id: uuid.UUID) -> Product | None:
        return await self.products.get_by_id(product_id)

    async def get_brand_ids(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, uuid.UUID]:
        result = await self.db.execute(
            select(Product.id, Product.brand_id).where(Product.id.in_(product_ids))
        )
        return {p_id: brand_id for p_id, brand_id in result.all() if brand_id}

    async def list_products_by_ids(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Product]:
        if not product_ids:
            return {}
        result = await self.db.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        return {p.id: p for p in result.scalars().all()}

    async def list_variants_by_ids(
        self, variant_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, ProductVariant]:
        if not variant_ids:
            return {}
        result = await self.db.execute(
            select(ProductVariant).where(ProductVariant.id.in_(variant_ids))
        )
        return {v.id: v for v in result.scalars().all()}

    async def list_sellers_by_ids(
        self, seller_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Seller]:
        if not seller_ids:
            return {}
        result = await self.db.execute(
            select(Seller).where(Seller.id.in_(seller_ids))
        )
        return {s.id: s for s in result.scalars().all()}

    async def list_attribute_values_for(
        self, variant_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[VariantAttributeValue]]:
        values = await self.variants.list_attribute_values_for_variants(variant_ids)
        grouped: dict[uuid.UUID, list[VariantAttributeValue]] = {}
        for value in values:
            grouped.setdefault(value.variant_id, []).append(value)
        return grouped

    async def list_attributes_by_ids(
        self, attribute_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, str]:
        """attribute_id -> attribute name. Used so variant attribute values
        come back with readable names (Color=Black, not just a UUID)."""
        if not attribute_ids:
            return {}
        from app.modules.products.models import Attribute

        result = await self.db.execute(
            select(Attribute).where(Attribute.id.in_(attribute_ids))
        )
        return {a.id: a.name for a in result.scalars().all()}

    async def list_images_by_product(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[ProductImage]]:
        if not product_ids:
            return {}
        result = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.product_id.in_(product_ids))
            .order_by(ProductImage.sort_order)
        )
        grouped: dict[uuid.UUID, list[ProductImage]] = {}
        for image in result.scalars().all():
            grouped.setdefault(image.product_id, []).append(image)
        return grouped

    async def list_active_listings_by_variants(
        self, variant_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[SellerListing]]:
        """variant_id -> its active listings (all active sellers offering
        it). Used by the product detail endpoint."""
        if not variant_ids:
            return {}
        result = await self.db.execute(
            select(SellerListing)
            .where(
                SellerListing.variant_id.in_(variant_ids),
                SellerListing.status == _ACTIVE,
            )
            .order_by(SellerListing.price.asc())
        )
        grouped: dict[uuid.UUID, list[SellerListing]] = {}
        for listing in result.scalars().all():
            grouped.setdefault(listing.variant_id, []).append(listing)
        return grouped

    async def list_active_variants_by_product(
        self, product_id: uuid.UUID
    ) -> list[ProductVariant]:
        result = await self.db.execute(
            select(ProductVariant)
            .where(
                ProductVariant.product_id == product_id,
                ProductVariant.status == _ACTIVE,
            )
            .order_by(ProductVariant.created_at)
        )
        return list(result.scalars().all())

    async def get_brand(self, brand_id: uuid.UUID) -> Brand | None:
        result = await self.db.execute(select(Brand).where(Brand.id == brand_id))
        return result.scalar_one_or_none()
