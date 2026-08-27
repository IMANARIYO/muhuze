import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import (
    CategoryCreateRequest,
    CategoryMoveRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.modules.categories.service import CategoryService


class CategoryController:
    """Translates HTTP requests/responses to and from the category service."""

    def __init__(self, db: AsyncSession) -> None:
        self.categories = CategoryService(CategoryRepository(db))

    async def get_category(self, category_id: uuid.UUID) -> CategoryResponse:
        category = await self.categories.get_by_id(category_id)
        return CategoryResponse.model_validate(category)

    async def list_categories(self) -> list[CategoryResponse]:
        categories = await self.categories.list_all()
        return [CategoryResponse.model_validate(category) for category in categories]

    async def list_top_level_categories(self) -> list[CategoryResponse]:
        categories = await self.categories.list_top_level()
        return [CategoryResponse.model_validate(category) for category in categories]

    async def list_children(self, category_id: uuid.UUID) -> list[CategoryResponse]:
        categories = await self.categories.list_children(category_id)
        return [CategoryResponse.model_validate(category) for category in categories]

    async def create_category(self, payload: CategoryCreateRequest) -> CategoryResponse:
        category = await self.categories.create(
            name=payload.name,
            description=payload.description,
            parent_id=payload.parent_id,
            sort_order=payload.sort_order,
        )
        return CategoryResponse.model_validate(category)

    async def update_category(
        self, category_id: uuid.UUID, payload: CategoryUpdateRequest
    ) -> CategoryResponse:
        category = await self.categories.update(
            category_id,
            name=payload.name,
            description=payload.description,
            sort_order=payload.sort_order,
            status=payload.status,
        )
        return CategoryResponse.model_validate(category)

    async def move_category(
        self, category_id: uuid.UUID, payload: CategoryMoveRequest
    ) -> CategoryResponse:
        category = await self.categories.move(
            category_id, parent_id=payload.parent_id
        )
        return CategoryResponse.model_validate(category)
