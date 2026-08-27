import uuid

from app.modules.categories.exceptions import (
    CategoryNotFoundError,
    CategoryParentNotFoundError,
    CircularParentError,
    DuplicateCategoryNameError,
    SelfParentError,
)
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository
from app.shared.utils.slugify import slugify


class CategoryService:
    """Business rules for categories. Slug generation/uniqueness lives
    here, not in the repository."""

    def __init__(self, categories: CategoryRepository) -> None:
        self.categories = categories

    async def get_by_id(self, category_id: uuid.UUID) -> Category:
        category = await self.categories.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError()
        return category

    async def list_all(self) -> list[Category]:
        return await self.categories.list_all()

    async def list_top_level(self) -> list[Category]:
        return await self.categories.list_top_level()

    async def list_children(self, parent_id: uuid.UUID) -> list[Category]:
        await self.get_by_id(parent_id)
        return await self.categories.list_children(parent_id)

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        parent_id: uuid.UUID | None,
        sort_order: int,
    ) -> Category:
        if parent_id is not None:
            parent = await self.categories.get_by_id(parent_id)
            if parent is None:
                raise CategoryParentNotFoundError()
        if await self.categories.name_exists_under_parent(
            parent_id=parent_id, name=name, exclude_id=None
        ):
            raise DuplicateCategoryNameError()
        slug = await self._unique_slug(name)
        return await self.categories.create(
            parent_id=parent_id,
            name=name,
            slug=slug,
            description=description,
            sort_order=sort_order,
        )

    async def update(
        self,
        category_id: uuid.UUID,
        *,
        name: str,
        description: str | None,
        sort_order: int,
        status: str,
    ) -> Category:
        category = await self.get_by_id(category_id)
        if (
            name != category.name
            and await self.categories.name_exists_under_parent(
                parent_id=category.parent_id, name=name, exclude_id=category_id
            )
        ):
            raise DuplicateCategoryNameError()
        return await self.categories.update(
            category,
            name=name,
            description=description,
            sort_order=sort_order,
            status=status,
        )

    async def move(
        self, category_id: uuid.UUID, *, parent_id: uuid.UUID | None
    ) -> Category:
        category = await self.get_by_id(category_id)
        if parent_id is not None:
            if parent_id == category_id:
                raise SelfParentError()
            parent = await self.categories.get_by_id(parent_id)
            if parent is None:
                raise CategoryParentNotFoundError()
            ancestors = await self.categories.get_ancestor_ids(category_id)
            if parent_id in ancestors:
                raise CircularParentError()
        if await self.categories.name_exists_under_parent(
            parent_id=parent_id, name=category.name, exclude_id=category_id
        ):
            raise DuplicateCategoryNameError()
        return await self.categories.move(category, parent_id=parent_id)

    async def _ensure_not_self_parent(
        self, category_id: uuid.UUID, parent_id: uuid.UUID
    ) -> None:
        if parent_id == category_id:
            raise SelfParentError()

    async def _unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while await self.categories.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug
