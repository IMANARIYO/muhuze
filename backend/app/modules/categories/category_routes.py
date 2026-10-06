import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.categories.category_dependencies import get_category_service
from app.modules.categories.category_permissions import CATEGORY_MANAGE, CATEGORY_MODERATE
from app.modules.categories.category_schema import (
    AttributeCreateRequest,
    AttributeResponse,
    AttributeUpdateRequest,
    CategoryCreateRequest,
    CategoryResponse,
    CategorySummaryResponse,
    CategoryUpdateRequest,
    OptionCreateRequest,
    OptionUpdateRequest,
    OwnCategoryFilters,
    StaffCategoryFilters,
)
from app.modules.categories.category_service import CategoryService
from app.modules.sellers.seller_dependencies import get_current_active_seller, get_seller_service
from app.modules.sellers.seller_model import Seller
from app.modules.sellers.seller_service import SellerService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

category_router = APIRouter(tags=["Categories"])

ServiceDep = Annotated[CategoryService, Depends(get_category_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
# The three gates of a seller action, in order (README §5.4): the permission,
# then an active seller. Ownership of the category is checked in the service.
CanManageDep = Annotated[Account, Depends(require_permission(CATEGORY_MANAGE))]
ActiveSellerDep = Annotated[Seller, Depends(get_current_active_seller)]
ModeratorDep = Annotated[Account, Depends(require_permission(CATEGORY_MODERATE))]


# ── What buyers see (no login needed) ────────────────────────────────────


@category_router.get(
    "/sellers/{seller_id}/categories", response_model=APIResponse[Page[CategoryResponse]]
)
async def list_shop_categories(
    seller_id: uuid.UUID,
    pagination: PaginationDep,
    service: ServiceDep,
    seller_service: Annotated[SellerService, Depends(get_seller_service)],
) -> JSONResponse:
    """The categories of a shop, with the attributes buyers can filter by.
    Public. A shop that isn't open looks like one that doesn't exist."""
    seller = await seller_service.get_open_shop(seller_id)
    page = await service.list_shop_categories(seller_id=seller.id, pagination=pagination)
    return success_response(data=page, message="Categories retrieved")


# ── A seller's own categories ────────────────────────────────────────────


@category_router.get("/categories/mine", response_model=APIResponse[Page[CategorySummaryResponse]])
async def list_my_categories(
    _: CanManageDep,
    seller: ActiveSellerDep,
    pagination: PaginationDep,
    filters: Annotated[OwnCategoryFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Your shop's categories, active or not, in your own order."""
    page = await service.list_own_categories(
        seller_id=seller.id, pagination=pagination, filters=filters
    )
    return success_response(data=page, message="Categories retrieved")


@category_router.post(
    "/categories", response_model=APIResponse[CategoryResponse], status_code=status.HTTP_201_CREATED
)
async def create_category(
    _: CanManageDep, seller: ActiveSellerDep, payload: CategoryCreateRequest, service: ServiceDep
) -> JSONResponse:
    """Add a category to your shop."""
    category = await service.create_category(seller_id=seller.id, payload=payload)
    return success_response(
        data=category, message="Category created", status_code=status.HTTP_201_CREATED
    )


@category_router.get("/categories/{category_id}", response_model=APIResponse[CategoryResponse])
async def get_my_category(
    _: CanManageDep, seller: ActiveSellerDep, category_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """One of your categories, with all its attributes and options."""
    category = await service.get_own_category(seller_id=seller.id, category_id=category_id)
    return success_response(data=category, message="Category retrieved")


@category_router.patch("/categories/{category_id}", response_model=APIResponse[CategoryResponse])
async def update_category(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Rename, describe, reorder, or switch a category on or off."""
    category = await service.update_category(
        seller_id=seller.id, category_id=category_id, payload=payload
    )
    return success_response(data=category, message="Category updated")


@category_router.delete("/categories/{category_id}", response_model=APIResponse[None])
async def delete_category(
    _: CanManageDep, seller: ActiveSellerDep, category_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Remove a category together with its attributes."""
    await service.delete_category(seller_id=seller.id, category_id=category_id)
    return success_response(message="Category deleted")


# ── Attributes ───────────────────────────────────────────────────────────


@category_router.post(
    "/categories/{category_id}/attributes",
    response_model=APIResponse[AttributeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_attribute(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    payload: AttributeCreateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Add something products in this category are described by, such as
    Storage or Colour. For a choice attribute, send its options too."""
    attribute = await service.add_attribute(
        seller_id=seller.id, category_id=category_id, payload=payload
    )
    return success_response(
        data=attribute, message="Attribute added", status_code=status.HTTP_201_CREATED
    )


@category_router.patch(
    "/categories/{category_id}/attributes/{attribute_id}",
    response_model=APIResponse[AttributeResponse],
)
async def update_attribute(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    attribute_id: uuid.UUID,
    payload: AttributeUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Change an attribute. Its type cannot be changed."""
    attribute = await service.update_attribute(
        seller_id=seller.id, category_id=category_id, attribute_id=attribute_id, payload=payload
    )
    return success_response(data=attribute, message="Attribute updated")


@category_router.delete(
    "/categories/{category_id}/attributes/{attribute_id}", response_model=APIResponse[None]
)
async def delete_attribute(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    attribute_id: uuid.UUID,
    service: ServiceDep,
) -> JSONResponse:
    await service.delete_attribute(
        seller_id=seller.id, category_id=category_id, attribute_id=attribute_id
    )
    return success_response(message="Attribute deleted")


# ── Options of a choice attribute ────────────────────────────────────────


@category_router.post(
    "/categories/{category_id}/attributes/{attribute_id}/options",
    response_model=APIResponse[AttributeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_option(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    attribute_id: uuid.UUID,
    payload: OptionCreateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Add an allowed value to a select or multi_select attribute."""
    attribute = await service.add_option(
        seller_id=seller.id, category_id=category_id, attribute_id=attribute_id, payload=payload
    )
    return success_response(
        data=attribute, message="Option added", status_code=status.HTTP_201_CREATED
    )


@category_router.patch(
    "/categories/{category_id}/attributes/{attribute_id}/options/{option_id}",
    response_model=APIResponse[AttributeResponse],
)
async def update_option(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    attribute_id: uuid.UUID,
    option_id: uuid.UUID,
    payload: OptionUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    attribute = await service.update_option(
        seller_id=seller.id,
        category_id=category_id,
        attribute_id=attribute_id,
        option_id=option_id,
        payload=payload,
    )
    return success_response(data=attribute, message="Option updated")


@category_router.delete(
    "/categories/{category_id}/attributes/{attribute_id}/options/{option_id}",
    response_model=APIResponse[AttributeResponse],
)
async def delete_option(
    _: CanManageDep,
    seller: ActiveSellerDep,
    category_id: uuid.UUID,
    attribute_id: uuid.UUID,
    option_id: uuid.UUID,
    service: ServiceDep,
) -> JSONResponse:
    attribute = await service.delete_option(
        seller_id=seller.id,
        category_id=category_id,
        attribute_id=attribute_id,
        option_id=option_id,
    )
    return success_response(data=attribute, message="Option deleted")


# ── Staff ────────────────────────────────────────────────────────────────


@category_router.get("/categories", response_model=APIResponse[Page[CategorySummaryResponse]])
async def list_all_categories(
    _: ModeratorDep,
    pagination: PaginationDep,
    filters: Annotated[StaffCategoryFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every shop's categories, for moderation."""
    page = await service.list_all_categories(pagination, filters)
    return success_response(data=page, message="Categories retrieved")


@category_router.post(
    "/categories/{category_id}/hide", response_model=APIResponse[CategorySummaryResponse]
)
async def hide_category(
    staff: ModeratorDep, category_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Hide a category that breaks the rules. Its seller cannot reactivate it."""
    category = await service.hide_category(category_id=category_id, staff_id=staff.id)
    return success_response(data=category, message="Category hidden")


@category_router.post(
    "/categories/{category_id}/restore", response_model=APIResponse[CategorySummaryResponse]
)
async def restore_category(
    staff: ModeratorDep, category_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Undo a staff hide."""
    category = await service.restore_category(category_id=category_id, staff_id=staff.id)
    return success_response(data=category, message="Category restored")
