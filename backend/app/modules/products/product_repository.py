"""Data access for products. No business rules, and no commits: the service
owns the transaction (AGENTS.md §13)."""

import uuid
from decimal import Decimal

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.product_constants import ProductStatus
from app.modules.products.product_model import Product, ProductAttributeValue, ProductImage
from app.shared.responses.pagination import PaginationParams

# The sort keys a client may ask for, mapped to real columns. Nothing else
# from the request ever reaches ORDER BY.
SORT_COLUMNS = {
    "created_at": Product.created_at,
    "published_at": Product.published_at,
    "price": Product.price,
    "name": func.lower(Product.name),
}


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Products ─────────────────────────────────────────────────────────

    async def get(self, product_id: uuid.UUID, *, for_update: bool = False) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        if for_update:
            # Serializes concurrent changes to one product, its images and values.
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def slugs_starting_with(
        self, seller_id: uuid.UUID, prefix: str, *, except_id: uuid.UUID | None = None
    ) -> set[str]:
        statement = select(Product.slug).where(
            Product.seller_id == seller_id, Product.slug.startswith(prefix, autoescape=True)
        )
        if except_id is not None:
            statement = statement.where(Product.id != except_id)
        return set(await self._session.scalars(statement))

    async def add(self, product: Product) -> None:
        self._session.add(product)
        await self._session.flush()

    async def delete(self, product: Product) -> None:
        await self._session.delete(product)
        await self._session.flush()

    async def list_products(
        self,
        pagination: PaginationParams,
        *,
        sort: str,
        seller_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        visible_to_buyers: tuple[Select, Select] | None = None,
    ) -> tuple[list[Product], int]:
        """`visible_to_buyers` is `(open shop ids, visible category ids)`:
        subqueries supplied by the sellers and categories features, which own
        those rules. When given, only products a buyer may see are returned."""
        statement = select(Product)
        if seller_id is not None:
            statement = statement.where(Product.seller_id == seller_id)
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if status is not None:
            statement = statement.where(Product.status == status)
        if search is not None:
            # autoescape: % and _ typed by the user match literally.
            statement = statement.where(Product.name.icontains(search, autoescape=True))
        if min_price is not None:
            statement = statement.where(Product.price >= min_price)
        if max_price is not None:
            statement = statement.where(Product.price <= max_price)
        if visible_to_buyers is not None:
            open_shops, visible_categories = visible_to_buyers
            statement = statement.where(
                Product.status == ProductStatus.PUBLISHED.value,
                Product.hidden_by_staff_at.is_(None),
                Product.seller_id.in_(open_shops),
                Product.category_id.in_(visible_categories),
            )

        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        column = SORT_COLUMNS[sort.removeprefix("-")]
        order = column.desc().nulls_last() if sort.startswith("-") else column.asc().nulls_last()
        rows = await self._session.scalars(
            # The id makes the order stable when two rows share the sort value.
            statement.order_by(order, Product.id).offset(pagination.offset).limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Images ───────────────────────────────────────────────────────────

    async def list_images(self, product_ids: list[uuid.UUID]) -> list[ProductImage]:
        """Images of several products in one query, each product's in display order."""
        if not product_ids:
            return []
        rows = await self._session.scalars(
            select(ProductImage)
            .where(ProductImage.product_id.in_(product_ids))
            .order_by(ProductImage.product_id, ProductImage.sort_order, ProductImage.created_at)
        )
        return list(rows)

    async def get_image(self, product_id: uuid.UUID, image_id: uuid.UUID) -> ProductImage | None:
        return await self._session.scalar(
            select(ProductImage).where(
                ProductImage.id == image_id, ProductImage.product_id == product_id
            )
        )

    async def add_image(self, image: ProductImage) -> None:
        self._session.add(image)
        await self._session.flush()

    async def delete_image(self, image: ProductImage) -> None:
        await self._session.delete(image)
        await self._session.flush()

    # ── Attribute values ─────────────────────────────────────────────────

    async def list_values(self, product_id: uuid.UUID) -> list[ProductAttributeValue]:
        rows = await self._session.scalars(
            select(ProductAttributeValue).where(ProductAttributeValue.product_id == product_id)
        )
        return list(rows)

    async def delete_values(
        self, product_id: uuid.UUID, *, attribute_ids: list[uuid.UUID] | None = None
    ) -> None:
        """Remove the product's values for the given attributes, or all of them."""
        statement = delete(ProductAttributeValue).where(
            ProductAttributeValue.product_id == product_id
        )
        if attribute_ids is not None:
            if not attribute_ids:
                return
            statement = statement.where(ProductAttributeValue.attribute_id.in_(attribute_ids))
        await self._session.execute(statement)

    async def add_values(self, values: list[ProductAttributeValue]) -> None:
        self._session.add_all(values)
        await self._session.flush()
