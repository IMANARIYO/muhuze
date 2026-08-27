import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category


class CategoryRepository:
    """Data access for categories. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def name_exists_under_parent(
        self, *, parent_id: uuid.UUID | None, name: str, exclude_id: uuid.UUID | None
    ) -> bool:
        """Check if a category with this name already exists under the given
        parent. Excludes the specified category (for update scenarios).
        Uses IS NULL for root categories since NULL = NULL is not TRUE in SQL."""
        if parent_id is None:
            query = select(Category.id).where(
                Category.name == name, Category.parent_id.is_(None)
            )
        else:
            query = select(Category.id).where(
                Category.name == name, Category.parent_id == parent_id
            )
        if exclude_id is not None:
            query = query.where(Category.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_ancestor_ids(self, category_id: uuid.UUID) -> list[uuid.UUID]:
        """Walk up the tree from a category, returning all ancestor IDs.
        Used for cycle detection when moving categories."""
        ancestors: list[uuid.UUID] = []
        current_id = category_id
        while True:
            result = await self.db.execute(
                select(Category.parent_id).where(Category.id == current_id)
            )
            parent_id = result.scalar_one_or_none()
            if parent_id is None:
                break
            ancestors.append(parent_id)
            current_id = parent_id
        return ancestors

    async def list_all(self) -> list[Category]:
        result = await self.db.execute(
            select(Category).order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars().all())

    async def list_top_level(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars().all())

    async def list_children(self, parent_id: uuid.UUID) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.parent_id == parent_id)
            .order_by(Category.sort_order, Category.name)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        parent_id: uuid.UUID | None,
        name: str,
        slug: str,
        description: str | None,
        sort_order: int,
    ) -> Category:
        category = Category(
            parent_id=parent_id,
            name=name,
            slug=slug,
            description=description,
            sort_order=sort_order,
        )
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(
        self,
        category: Category,
        *,
        name: str,
        description: str | None,
        sort_order: int,
        status: str,
    ) -> Category:
        category.name = name
        category.description = description
        category.sort_order = sort_order
        category.status = status
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def move(
        self, category: Category, *, parent_id: uuid.UUID | None
    ) -> Category:
        category.parent_id = parent_id
        await self.db.flush()
        await self.db.refresh(category)
        return category
