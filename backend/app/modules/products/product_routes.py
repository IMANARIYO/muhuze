import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.products.product_constants import IMAGE_MAX_BYTES
from app.modules.products.product_dependencies import get_product_service
from app.modules.products.product_permissions import PRODUCT_MANAGE, PRODUCT_MODERATE
from app.modules.products.product_schema import (
    ImageOrderRequest,
    OwnProductFilters,
    OwnProductResponse,
    ProductCreateRequest,
    ProductResponse,
    ProductSummaryResponse,
    ProductUpdateRequest,
    PublicProductFilters,
    PublicProductResponse,
    StaffProductFilters,
)
from app.modules.products.product_service import ProductService
from app.modules.sellers.seller_dependencies import get_current_active_seller
from app.modules.sellers.seller_model import Seller
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

product_router = APIRouter(prefix="/products", tags=["Products"])

ServiceDep = Annotated[ProductService, Depends(get_product_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
# The three gates of a seller action, in order (README §5.4): the permission,
# then an active seller. Ownership of the product is checked in the service.
CanManageDep = Annotated[Account, Depends(require_permission(PRODUCT_MANAGE))]
ActiveSellerDep = Annotated[Seller, Depends(get_current_active_seller)]
ModeratorDep = Annotated[Account, Depends(require_permission(PRODUCT_MODERATE))]

# Fixed paths ("/mine", "/moderation") are declared before "/{product_id}" so
# they are never read as an id.

# ── A seller's own products ──────────────────────────────────────────────


@product_router.get("/mine", response_model=APIResponse[Page[ProductSummaryResponse]])
async def list_my_products(
    _: CanManageDep,
    seller: ActiveSellerDep,
    pagination: PaginationDep,
    filters: Annotated[OwnProductFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Your shop's products in any status."""
    page = await service.list_own_products(
        seller_id=seller.id, pagination=pagination, filters=filters
    )
    return success_response(data=page, message="Products retrieved")


@product_router.post(
    "", response_model=APIResponse[OwnProductResponse], status_code=status.HTTP_201_CREATED
)
async def create_product(
    _: CanManageDep, seller: ActiveSellerDep, payload: ProductCreateRequest, service: ServiceDep
) -> JSONResponse:
    """Start a product as a draft. Add images, then publish it."""
    product = await service.create_product(seller_id=seller.id, payload=payload)
    return success_response(
        data=product, message="Product created as a draft", status_code=status.HTTP_201_CREATED
    )


@product_router.get("/mine/{product_id}", response_model=APIResponse[OwnProductResponse])
async def get_my_product(
    _: CanManageDep, seller: ActiveSellerDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """One of your products, with what still stops it being published."""
    product = await service.get_own_product(seller_id=seller.id, product_id=product_id)
    return success_response(data=product, message="Product retrieved")


@product_router.patch("/mine/{product_id}", response_model=APIResponse[OwnProductResponse])
async def update_product(
    _: CanManageDep,
    seller: ActiveSellerDep,
    product_id: uuid.UUID,
    payload: ProductUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Change a product. A published product must stay complete."""
    product = await service.update_product(
        seller_id=seller.id, product_id=product_id, payload=payload
    )
    return success_response(data=product, message="Product updated")


@product_router.delete("/mine/{product_id}", response_model=APIResponse[None])
async def delete_product(
    _: CanManageDep, seller: ActiveSellerDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Delete a draft that was never published. Archive anything else."""
    await service.delete_product(seller_id=seller.id, product_id=product_id)
    return success_response(message="Product deleted")


@product_router.post("/mine/{product_id}/publish", response_model=APIResponse[OwnProductResponse])
async def publish_product(
    _: CanManageDep, seller: ActiveSellerDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Put a draft or archived product on sale."""
    product = await service.publish(seller_id=seller.id, product_id=product_id)
    return success_response(data=product, message="Product published")


@product_router.post("/mine/{product_id}/archive", response_model=APIResponse[OwnProductResponse])
async def archive_product(
    _: CanManageDep, seller: ActiveSellerDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Take a published product off sale. It can be published again."""
    product = await service.archive(seller_id=seller.id, product_id=product_id)
    return success_response(data=product, message="Product archived")


# ── Images ───────────────────────────────────────────────────────────────


@product_router.post(
    "/mine/{product_id}/images",
    response_model=APIResponse[OwnProductResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_product_image(
    _: CanManageDep,
    seller: ActiveSellerDep,
    product_id: uuid.UUID,
    file: UploadFile,
    service: ServiceDep,
) -> JSONResponse:
    """Add a picture (JPEG or PNG, up to 5 MB) as multipart form field `file`.
    It goes after the existing ones; the first picture is the main one."""
    # One byte past the limit is enough to know the file is too large.
    content = await file.read(IMAGE_MAX_BYTES + 1)
    product = await service.add_image(seller_id=seller.id, product_id=product_id, content=content)
    return success_response(
        data=product, message="Image added", status_code=status.HTTP_201_CREATED
    )


@product_router.put(
    "/mine/{product_id}/images/order", response_model=APIResponse[OwnProductResponse]
)
async def reorder_product_images(
    _: CanManageDep,
    seller: ActiveSellerDep,
    product_id: uuid.UUID,
    payload: ImageOrderRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Set the order of the pictures. The first becomes the main picture."""
    product = await service.reorder_images(
        seller_id=seller.id, product_id=product_id, image_ids=payload.image_ids
    )
    return success_response(data=product, message="Images reordered")


@product_router.delete(
    "/mine/{product_id}/images/{image_id}", response_model=APIResponse[OwnProductResponse]
)
async def delete_product_image(
    _: CanManageDep,
    seller: ActiveSellerDep,
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    service: ServiceDep,
) -> JSONResponse:
    product = await service.delete_image(
        seller_id=seller.id, product_id=product_id, image_id=image_id
    )
    return success_response(data=product, message="Image removed")


# ── Staff ────────────────────────────────────────────────────────────────


@product_router.get("/moderation", response_model=APIResponse[Page[ProductSummaryResponse]])
async def list_all_products(
    _: ModeratorDep,
    pagination: PaginationDep,
    filters: Annotated[StaffProductFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every shop's products in any status, for moderation."""
    page = await service.list_all_products(pagination, filters)
    return success_response(data=page, message="Products retrieved")


@product_router.get("/moderation/{product_id}", response_model=APIResponse[ProductResponse])
async def get_any_product(
    _: ModeratorDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Any product in any status, as its seller entered it."""
    product = await service.get_any_product(product_id)
    return success_response(data=product, message="Product retrieved")


@product_router.post(
    "/moderation/{product_id}/hide", response_model=APIResponse[ProductSummaryResponse]
)
async def hide_product(
    staff: ModeratorDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Hide a product that breaks the rules. Its seller cannot publish it."""
    product = await service.hide_product(product_id=product_id, staff_id=staff.id)
    return success_response(data=product, message="Product hidden")


@product_router.post(
    "/moderation/{product_id}/restore", response_model=APIResponse[ProductSummaryResponse]
)
async def restore_product(
    staff: ModeratorDep, product_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Undo a staff hide."""
    product = await service.restore_product(product_id=product_id, staff_id=staff.id)
    return success_response(data=product, message="Product restored")


# ── What buyers see (no login needed) ────────────────────────────────────


@product_router.get("", response_model=APIResponse[Page[ProductSummaryResponse]])
async def list_products(
    pagination: PaginationDep,
    filters: Annotated[PublicProductFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Products on sale across every open shop. Filter by shop, category,
    price range, or name."""
    page = await service.list_public_products(pagination, filters)
    return success_response(data=page, message="Products retrieved")


@product_router.get("/{product_id}", response_model=APIResponse[PublicProductResponse])
async def get_product(product_id: uuid.UUID, service: ServiceDep) -> JSONResponse:
    """A product on sale, with its pictures, details, and shop."""
    return success_response(
        data=await service.get_public_product(product_id), message="Product retrieved"
    )
