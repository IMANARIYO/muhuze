import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import require_role
from app.modules.auth.models import Account
from app.modules.categories.controller import CategoryController
from app.modules.categories.dependencies import get_category_controller
from app.modules.categories.schemas import (
    CategoryCreateRequest,
    CategoryMoveRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
async def list_categories(
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[list[CategoryResponse]]:
    """List every category, flat (not nested) — use `parent_id` on each
    row to reconstruct the tree, or /roots and /{id}/children to walk it
    level by level."""
    categories = await controller.list_categories()
    return success_response(
        data=categories, message="Categories retrieved successfully"
    )


@router.get("/roots")
async def list_top_level_categories(
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[list[CategoryResponse]]:
    """List only top-level categories (`parent_id` is null)."""
    categories = await controller.list_top_level_categories()
    return success_response(
        data=categories, message="Top-level categories retrieved successfully"
    )


@router.get("/{category_id}")
async def get_category(
    category_id: uuid.UUID,
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[CategoryResponse]:
    """Get one category by id."""
    category = await controller.get_category(category_id)
    return success_response(data=category, message="Category retrieved successfully")


@router.get("/{category_id}/children")
async def list_children(
    category_id: uuid.UUID,
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[list[CategoryResponse]]:
    """List the direct children of a category (not grandchildren)."""
    categories = await controller.list_children(category_id)
    return success_response(
        data=categories, message="Subcategories retrieved successfully"
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[CategoryResponse]:
    """Create a category, optionally under a `parent_id`. `slug` is
    auto-generated from `name` (numeric suffix on collision). Admin only —
    sellers pick from the existing tree rather than creating categories
    themselves, to keep the catalog from fragmenting."""
    category = await controller.create_category(payload)
    return success_response(data=category, message="Category created successfully")


@router.patch("/{category_id}")
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[CategoryResponse]:
    """Update a category's name, description, or status. Admin only."""
    category = await controller.update_category(category_id, payload)
    return success_response(data=category, message="Category updated successfully")


@router.patch("/{category_id}/move")
async def move_category(
    category_id: uuid.UUID,
    payload: CategoryMoveRequest,
    admin: Account = Depends(require_role("admin")),
    controller: CategoryController = Depends(get_category_controller),
) -> APIResponse[CategoryResponse]:
    """Move a category to a new parent. Set `parent_id` to null to move
    to top-level. Rejects self-parent, circular relationships, and
    duplicate names under the same parent. Admin only."""
    category = await controller.move_category(category_id, payload)
    return success_response(data=category, message="Category moved successfully")
