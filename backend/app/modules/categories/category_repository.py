"""Data access for categories. No business rules, and no commits: the
service owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.category_model import (
    Category,
    CategoryAttribute,
    CategoryAttributeOption,
)
from app.shared.responses.pagination import PaginationParams


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Categories ───────────────────────────────────────────────────────

    async def get(self, category_id: uuid.UUID, *, for_update: bool = False) -> Category | None:
        statement = select(Category).where(Category.id == category_id)
        if for_update:
            # Serializes concurrent changes to one category and its attributes.
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def name_exists(
        self, seller_id: uuid.UUID, name: str, *, except_id: uuid.UUID | None = None
    ) -> bool:
        statement = select(Category.id).where(
            Category.seller_id == seller_id, func.lower(Category.name) == name.lower()
        )
        if except_id is not None:
            statement = statement.where(Category.id != except_id)
        return await self._session.scalar(statement) is not None

    async def slugs_starting_with(
        self, seller_id: uuid.UUID, prefix: str, *, except_id: uuid.UUID | None = None
    ) -> set[str]:
        statement = select(Category.slug).where(
            Category.seller_id == seller_id, Category.slug.startswith(prefix, autoescape=True)
        )
        if except_id is not None:
            statement = statement.where(Category.id != except_id)
        return set(await self._session.scalars(statement))

    async def add(self, category: Category) -> None:
        self._session.add(category)
        await self._session.flush()

    async def delete(self, category: Category) -> None:
        await self._session.delete(category)
        await self._session.flush()

    async def list_categories(
        self,
        pagination: PaginationParams,
        *,
        seller_id: uuid.UUID | None,
        is_active: bool | None,
        search: str | None,
    ) -> tuple[list[Category], int]:
        statement = select(Category)
        if seller_id is not None:
            statement = statement.where(Category.seller_id == seller_id)
        if is_active is not None:
            statement = statement.where(Category.is_active.is_(is_active))
        if search is not None:
            # autoescape: % and _ typed by the user match literally.
            statement = statement.where(Category.name.icontains(search, autoescape=True))

        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            # The seller's own order, then the name; the id keeps pages stable.
            statement.order_by(Category.sort_order, func.lower(Category.name), Category.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Attributes ───────────────────────────────────────────────────────

    async def get_attribute(
        self, category_id: uuid.UUID, attribute_id: uuid.UUID
    ) -> CategoryAttribute | None:
        return await self._session.scalar(
            select(CategoryAttribute).where(
                CategoryAttribute.id == attribute_id, CategoryAttribute.category_id == category_id
            )
        )

    async def attribute_codes(self, category_id: uuid.UUID) -> set[str]:
        return set(
            await self._session.scalars(
                select(CategoryAttribute.code).where(CategoryAttribute.category_id == category_id)
            )
        )

    async def attribute_name_exists(
        self, category_id: uuid.UUID, name: str, *, except_id: uuid.UUID | None = None
    ) -> bool:
        statement = select(CategoryAttribute.id).where(
            CategoryAttribute.category_id == category_id,
            func.lower(CategoryAttribute.name) == name.lower(),
        )
        if except_id is not None:
            statement = statement.where(CategoryAttribute.id != except_id)
        return await self._session.scalar(statement) is not None

    async def list_attributes(
        self, category_ids: list[uuid.UUID], *, active_only: bool = False
    ) -> list[CategoryAttribute]:
        """Attributes of several categories in one query, in display order."""
        if not category_ids:
            return []
        statement = select(CategoryAttribute).where(CategoryAttribute.category_id.in_(category_ids))
        if active_only:
            statement = statement.where(CategoryAttribute.is_active.is_(True))
        rows = await self._session.scalars(
            statement.order_by(
                CategoryAttribute.sort_order,
                func.lower(CategoryAttribute.name),
                CategoryAttribute.id,
            )
        )
        return list(rows)

    async def add_attribute(self, attribute: CategoryAttribute) -> None:
        self._session.add(attribute)
        await self._session.flush()

    async def delete_attribute(self, attribute: CategoryAttribute) -> None:
        await self._session.delete(attribute)
        await self._session.flush()

    # ── Options ──────────────────────────────────────────────────────────

    async def get_option(
        self, attribute_id: uuid.UUID, option_id: uuid.UUID
    ) -> CategoryAttributeOption | None:
        return await self._session.scalar(
            select(CategoryAttributeOption).where(
                CategoryAttributeOption.id == option_id,
                CategoryAttributeOption.attribute_id == attribute_id,
            )
        )

    async def option_value_exists(
        self, attribute_id: uuid.UUID, value: str, *, except_id: uuid.UUID | None = None
    ) -> bool:
        statement = select(CategoryAttributeOption.id).where(
            CategoryAttributeOption.attribute_id == attribute_id,
            func.lower(CategoryAttributeOption.value) == value.lower(),
        )
        if except_id is not None:
            statement = statement.where(CategoryAttributeOption.id != except_id)
        return await self._session.scalar(statement) is not None

    async def list_options(
        self, attribute_ids: list[uuid.UUID], *, active_only: bool = False
    ) -> list[CategoryAttributeOption]:
        """Options of several attributes in one query, in display order."""
        if not attribute_ids:
            return []
        statement = select(CategoryAttributeOption).where(
            CategoryAttributeOption.attribute_id.in_(attribute_ids)
        )
        if active_only:
            statement = statement.where(CategoryAttributeOption.is_active.is_(True))
        rows = await self._session.scalars(
            statement.order_by(
                CategoryAttributeOption.sort_order,
                func.lower(CategoryAttributeOption.value),
                CategoryAttributeOption.id,
            )
        )
        return list(rows)

    async def add_options(self, options: list[CategoryAttributeOption]) -> None:
        self._session.add_all(options)
        await self._session.flush()

    async def delete_option(self, option: CategoryAttributeOption) -> None:
        await self._session.delete(option)
        await self._session.flush()
