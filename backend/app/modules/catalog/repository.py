import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category
from app.modules.products.models import (
    Attribute,
    Brand,
    CategoryAttribute,
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

    async def get_category_ids_including_descendants(
        self, category_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """The given category plus every descendant, via a recursive CTE.
        Used so a category filter also surfaces products in its subcategories
        (Electronics -> Phones -> Smartphones).

        Built from the ORM model (not raw text) so `Category.id`'s UUID type
        drives both the bound root value and the read-back rows through the
        dialect's bind/result processors — required because SQLite stores
        UUIDs as their `hex` form while Postgres stores a native UUID."""
        category_cte = (
            select(Category.id).where(Category.id == category_id)
            # .cte(recursive=True) marks the seed; the recursive term is added
            # with .union_all() below, as SQLAlchemy 2.x requires.
            .cte(name="subtree", recursive=True)
        )
        category_cte = category_cte.union_all(
            select(Category.id)
            .join(category_cte, Category.parent_id == category_cte.c.id)
        )
        result = await self.db.execute(select(category_cte.c.id))
        return list(result.scalars().all())

    def _variant_ids_for_attribute_filters(
        self,
        query,
        filters,
    ):
        """Apply `attribute_id`+value pairs (parallel lists, zipped by index)
        to a variant-id subquery. Each pair must match on the same variant, so
        they are AND-ed together against variant_attribute_values."""
        attribute_ids = filters.get("attribute_ids") or []
        values = filters.get("attribute_values") or []
        for attribute_id, value in zip(attribute_ids, values):
            query = query.where(
                VariantAttributeValue.variant_id.in_(
                    select(VariantAttributeValue.variant_id).where(
                        VariantAttributeValue.attribute_id == attribute_id,
                        VariantAttributeValue.value == value,
                    )
                )
            )
        return query

    async def list_active_listings(
        self,
        *,
        category_ids: list[uuid.UUID] | None,
        brand_id: uuid.UUID | None,
        search: str | None,
        sort: str | None,
        min_price: float | None,
        max_price: float | None,
        conditions: list[str] | None,
        in_stock: bool,
        filters: dict | None,
    ) -> list[SellerListing]:
        query = select(SellerListing).where(SellerListing.status == _ACTIVE)

        product_ids: list[uuid.UUID] | None = None
        product_query = select(Product.id)

        product_filters = []
        if category_ids:
            product_filters.append(Product.category_id.in_(category_ids))
        if brand_id is not None:
            product_filters.append(Product.brand_id == brand_id)
        if search is not None:
            product_filters.append(
                Product.name.ilike(f"%{search}%")
                | Product.id.in_(
                    select(Product.id)
                    .join(Brand, Product.brand_id == Brand.id)
                    .where(Brand.name.ilike(f"%{search}%"))
                )
                | Product.id.in_(
                    select(Product.id)
                    .join(Category, Product.category_id == Category.id)
                    .where(Category.name.ilike(f"%{search}%"))
                )
            )
        if product_filters:
            for pf in product_filters:
                product_query = product_query.where(pf)
            product_ids = list(
                (await self.db.execute(product_query)).scalars().all()
            )
            if not product_ids:
                return []

        # Base active product/variant scope (only active variants, and only
        # variants of the matched products when a product-level filter applied).
        variant_query = select(ProductVariant.id).where(
            ProductVariant.status == _ACTIVE
        )
        if product_ids is not None:
            variant_query = variant_query.where(
                ProductVariant.product_id.in_(product_ids)
            )
        variant_query = self._variant_ids_for_attribute_filters(
            variant_query, filters or {}
        )
        variant_ids = list(
            (await self.db.execute(variant_query)).scalars().all()
        )
        if not variant_ids:
            return []
        query = query.where(SellerListing.variant_id.in_(variant_ids))

        if min_price is not None:
            query = query.where(SellerListing.price >= min_price)
        if max_price is not None:
            query = query.where(SellerListing.price <= max_price)
        if conditions:
            query = query.where(SellerListing.condition.in_(conditions))
        if in_stock:
            query = query.where(SellerListing.stock > 0)

        if sort == "price_desc":
            query = query.order_by(
                SellerListing.price.desc(), SellerListing.created_at.desc()
            )
        elif sort == "newest":
            query = query.order_by(SellerListing.created_at.desc())
        else:
            query = query.order_by(
                SellerListing.price.asc(), SellerListing.created_at.desc()
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_product_detail(self, product_id: uuid.UUID) -> Product | None:
        return await self.products.get_by_id(product_id)

    async def get_active_variant_ids_in_categories(
        self, category_ids: list[uuid.UUID]
    ) -> list[uuid.UUID]:
        """IDs of active variants whose product belongs to the category set."""
        if not category_ids:
            return []
        product_ids = select(Product.id).where(Product.category_id.in_(category_ids))
        result = await self.db.execute(
            select(ProductVariant.id)
            .where(
                ProductVariant.product_id.in_(product_ids),
                ProductVariant.status == _ACTIVE,
            )
        )
        return list(result.scalars().all())

    async def get_filter_brands(
        self, category_ids: list[uuid.UUID]
    ) -> list[Brand]:
        """Active brands that actually have an active offer in the category."""
        product_ids = select(Product.id).where(Product.category_id.in_(category_ids))
        variant_ids = select(ProductVariant.id).where(
            ProductVariant.product_id.in_(product_ids),
            ProductVariant.status == _ACTIVE,
        )
        listing_variant_ids = select(SellerListing.variant_id).where(
            SellerListing.variant_id.in_(variant_ids),
            SellerListing.status == _ACTIVE,
        )
        result = await self.db.execute(
            select(Brand).where(
                Brand.id.in_(
                    select(Product.brand_id)
                    .where(
                        Product.id.in_(
                            select(ProductVariant.product_id).where(
                                ProductVariant.id.in_(listing_variant_ids)
                            )
                        ),
                        Product.brand_id.is_not(None),
                    )
                ),
                Brand.status == _ACTIVE,
            ).order_by(Brand.name)
        )
        return list(result.scalars().all())

    async def get_filterable_attributes(
        self, category_ids: list[uuid.UUID]
    ) -> list[CategoryAttribute]:
        """The category_attributes marked filterable for the category tree."""
        child_ids = select(Category.id).where(
            Category.parent_id.in_(category_ids)
        )
        all_cat_ids = category_ids + list(
            (await self.db.execute(child_ids)).scalars().all()
        )
        result = await self.db.execute(
            select(CategoryAttribute)
            .where(
                CategoryAttribute.category_id.in_(all_cat_ids),
                CategoryAttribute.is_filterable.is_(True),
            )
            .order_by(CategoryAttribute.sort_order)
        )
        return list(result.scalars().all())

    async def get_filter_values(
        self,
        variant_ids: list[uuid.UUID],
        attribute_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, list[str]]:
        """attribute_id -> distinct values from the active variants that carry
        a filterable attribute."""
        if not variant_ids or not attribute_ids:
            return {}
        result = await self.db.execute(
            select(VariantAttributeValue.attribute_id, VariantAttributeValue.value)
            .where(
                VariantAttributeValue.variant_id.in_(variant_ids),
                VariantAttributeValue.attribute_id.in_(attribute_ids),
            )
            .distinct()
            .order_by(VariantAttributeValue.value)
        )
        grouped: dict[uuid.UUID, list[str]] = {}
        for attribute_id, value in result.all():
            grouped.setdefault(attribute_id, []).append(value)
        return grouped

    async def get_filter_price_range(
        self, category_ids: list[uuid.UUID]
    ) -> tuple[float, float] | None:
        product_ids = select(Product.id).where(Product.category_id.in_(category_ids))
        variant_ids = select(ProductVariant.id).where(
            ProductVariant.product_id.in_(product_ids),
            ProductVariant.status == _ACTIVE,
        )
        listing_ids = select(SellerListing.id).where(
            SellerListing.variant_id.in_(variant_ids),
            SellerListing.status == _ACTIVE,
        )
        result = await self.db.execute(
            select(
                func.min(SellerListing.price), func.max(SellerListing.price)
            ).where(SellerListing.id.in_(listing_ids))
        )
        lo, hi = result.one()
        if lo is None or hi is None:
            return None
        return float(lo), float(hi)

    async def get_filter_conditions(
        self, category_ids: list[uuid.UUID]
    ) -> list[str]:
        product_ids = select(Product.id).where(Product.category_id.in_(category_ids))
        variant_ids = select(ProductVariant.id).where(
            ProductVariant.product_id.in_(product_ids),
            ProductVariant.status == _ACTIVE,
        )
        result = await self.db.execute(
            select(SellerListing.condition)
            .where(
                SellerListing.variant_id.in_(variant_ids),
                SellerListing.status == _ACTIVE,
            )
            .distinct()
            .order_by(SellerListing.condition)
        )
        return list(result.scalars().all())

    async def get_attributes_by_ids(
        self, attribute_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Attribute]:
        if not attribute_ids:
            return {}
        result = await self.db.execute(
            select(Attribute).where(Attribute.id.in_(attribute_ids))
        )
        return {a.id: a for a in result.scalars().all()}

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
