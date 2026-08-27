import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.modules.auth.dependencies import get_current_account, require_role
from app.modules.auth.models import Account
from app.modules.products.controller import (
    AttributeController,
    BrandController,
    ListingController,
    ProductController,
)
from app.modules.products.dependencies import (
    ProductActor,
    get_attribute_controller,
    get_brand_controller,
    get_listing_controller,
    get_product_controller,
    require_admin_or_active_seller,
)
from app.modules.products.schemas import (
    AttributeCreateRequest,
    AttributeResponse,
    AttributeUpdateRequest,
    BrandCreateRequest,
    BrandResponse,
    BrandUpdateRequest,
    ListingImageResponse,
    ProductCreateRequest,
    ProductImageResponse,
    ProductResponse,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantResponse,
    ProductVariantUpdateRequest,
    RejectListingRequest,
    RejectProductRequest,
    SellerListingCreateRequest,
    SellerListingResponse,
    SellerListingUpdatePriceRequest,
    SellerListingUpdateRequest,
    SellerListingUpdateStockRequest,
)
from app.modules.sellers.dependencies import get_current_seller
from app.modules.sellers.models import Seller
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

brands_router = APIRouter(prefix="/brands", tags=["Brands"])
attributes_router = APIRouter(prefix="/attributes", tags=["Attributes"])
products_router = APIRouter(prefix="/products", tags=["Products"])
listings_router = APIRouter(prefix="/listings", tags=["Seller Listings"])


# --- brands ------------------------------------------------------------------


@brands_router.get("")
async def list_brands(
    controller: BrandController = Depends(get_brand_controller),
) -> APIResponse[list[BrandResponse]]:
    """List every brand."""
    brands = await controller.list_brands()
    return success_response(data=brands, message="Brands retrieved successfully")


@brands_router.get("/{brand_id}")
async def get_brand(
    brand_id: uuid.UUID,
    controller: BrandController = Depends(get_brand_controller),
) -> APIResponse[BrandResponse]:
    """Get one brand by id."""
    brand = await controller.get_brand(brand_id)
    return success_response(data=brand, message="Brand retrieved successfully")


@brands_router.post("", status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: BrandController = Depends(get_brand_controller),
) -> APIResponse[BrandResponse]:
    """Create a brand. `name` must be unique; `slug` is auto-generated.
    Admin only — brands are a controlled vocabulary so "Samsung" /
    "samsung" / "Samsung Inc" don't end up as three different rows."""
    brand = await controller.create_brand(payload)
    return success_response(data=brand, message="Brand created successfully")


@brands_router.patch("/{brand_id}")
async def update_brand(
    brand_id: uuid.UUID,
    payload: BrandUpdateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: BrandController = Depends(get_brand_controller),
) -> APIResponse[BrandResponse]:
    """Update a brand's name, description, or status. Admin only."""
    brand = await controller.update_brand(brand_id, payload)
    return success_response(data=brand, message="Brand updated successfully")


# --- attributes ----------------------------------------------------------


@attributes_router.get("")
async def list_attributes(
    controller: AttributeController = Depends(get_attribute_controller),
) -> APIResponse[list[AttributeResponse]]:
    """List every attribute (Color, RAM, Size, etc.) — the vocabulary
    variants are built from."""
    attributes = await controller.list_attributes()
    return success_response(
        data=attributes, message="Attributes retrieved successfully"
    )


@attributes_router.get("/{attribute_id}")
async def get_attribute(
    attribute_id: uuid.UUID,
    controller: AttributeController = Depends(get_attribute_controller),
) -> APIResponse[AttributeResponse]:
    """Get one attribute by id."""
    attribute = await controller.get_attribute(attribute_id)
    return success_response(data=attribute, message="Attribute retrieved successfully")


@attributes_router.post("", status_code=status.HTTP_201_CREATED)
async def create_attribute(
    payload: AttributeCreateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AttributeController = Depends(get_attribute_controller),
) -> APIResponse[AttributeResponse]:
    """Create an attribute definition. `slug` is auto-generated from
    `name`. Admin only — attributes are a global, admin-curated
    vocabulary; sellers pick from existing attributes when defining a
    variant rather than inventing free-text fields."""
    attribute = await controller.create_attribute(payload)
    return success_response(data=attribute, message="Attribute created successfully")


@attributes_router.patch("/{attribute_id}")
async def update_attribute(
    attribute_id: uuid.UUID,
    payload: AttributeUpdateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AttributeController = Depends(get_attribute_controller),
) -> APIResponse[AttributeResponse]:
    """Update an attribute's name, input type, unit, or status. Admin
    only."""
    attribute = await controller.update_attribute(attribute_id, payload)
    return success_response(data=attribute, message="Attribute updated successfully")


# --- products --------------------------------------------------------------


@products_router.get("")
async def list_products(
    category_id: uuid.UUID | None = Query(default=None),
    brand_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(
        default=None, description="Case-insensitive substring match on product name"
    ),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[list[ProductResponse]]:
    """List products, optionally filtered by category, brand, status
    (`?status=active`), and/or name search — use `search` to check
    whether a product already exists before requesting a new one."""
    products = await controller.list_products(
        category_id=category_id, brand_id=brand_id, status=status_filter, search=search
    )
    return success_response(data=products, message="Products retrieved successfully")


@products_router.get("/mine")
async def list_my_products(
    seller: Seller = Depends(get_current_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[list[ProductResponse]]:
    """List the products the caller (as an active seller) has requested,
    in any status — including drafts and rejections nobody else can
    see."""
    products = await controller.list_my_products(seller.id)
    return success_response(
        data=products, message="Your product requests retrieved successfully"
    )


@products_router.get("/{product_id}")
async def get_product(
    product_id: uuid.UUID,
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Get one product (SPU) by id. Does not include variants — see
    /{product_id}/variants."""
    product = await controller.get_product(product_id)
    return success_response(data=product, message="Product retrieved successfully")


@products_router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Create a product (SPU) in `draft` status. `category_id` must
    exist; `brand_id` is optional but must exist if given. Callable by an
    admin (curates the catalog directly) or any active seller (requests
    a new product — tagged as theirs, and only they or an admin can edit
    or submit it until it's approved). See
    products/docs/product-lifecycle.md."""
    product = await controller.create_product(
        payload, created_by_seller_id=actor.seller_id
    )
    return success_response(data=product, message="Product created successfully")


@products_router.patch("/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdateRequest,
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Update a product's category, brand, name, or description. Only
    allowed while `draft` or `rejected` — 409 otherwise. Admin can edit
    any product; a seller can only edit a product they themselves
    requested (403 otherwise)."""
    product = await controller.update_product(
        product_id, payload, requester_seller_id=actor.seller_id
    )
    return success_response(data=product, message="Product updated successfully")


@products_router.post("/{product_id}/submit")
async def submit_for_review(
    product_id: uuid.UUID,
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Move a product from `draft`/`rejected` to `pending_review`.
    Callable by admin on any product, or by the requesting seller on
    their own (403 otherwise)."""
    product = await controller.submit_for_review(
        product_id, requester_seller_id=actor.seller_id
    )
    return success_response(data=product, message="Product submitted for review")


@products_router.post("/{product_id}/approve")
async def approve(
    product_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Approve a `pending_review` product, moving it to `active` and
    making it visible in the catalog. Admin only."""
    product = await controller.approve(product_id)
    return success_response(data=product, message="Product approved successfully")


@products_router.post("/{product_id}/reject")
async def reject(
    product_id: uuid.UUID,
    payload: RejectProductRequest,
    admin: Account = Depends(require_role("admin")),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Reject a `pending_review` product with a reason, moving it to
    `rejected` (editable again for resubmission). Admin only."""
    product = await controller.reject(product_id, payload)
    return success_response(data=product, message="Product rejected")


@products_router.post("/{product_id}/archive")
async def archive(
    product_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductResponse]:
    """Archive an `active` product, removing it from buyer-facing
    listings without deleting it. Admin only."""
    product = await controller.archive(product_id)
    return success_response(data=product, message="Product archived")


# --- variants ----------------------------------------------------------------


@products_router.get("/{product_id}/variants")
async def list_variants(
    product_id: uuid.UUID,
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[list[ProductVariantResponse]]:
    """List a product's variants (SKUs), each with its attribute
    values."""
    variants = await controller.list_variants(product_id)
    return success_response(data=variants, message="Variants retrieved successfully")


@products_router.post("/{product_id}/variants", status_code=status.HTTP_201_CREATED)
async def create_variant(
    product_id: uuid.UUID,
    payload: ProductVariantCreateRequest,
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductVariantResponse]:
    """Create a variant (SKU) with its attribute values (e.g. Color=Black,
    Storage=256GB). Rejects a combination of attribute values already
    used by another variant of the same product (422), and rejects the
    same attribute supplied twice in one request (422). Admin, or any
    active seller once the product is `active` (shared catalog — that's
    what lets a seller add "also comes in Blue" nobody's requested yet);
    before that, only the requesting seller or admin (403 otherwise)."""
    variant = await controller.create_variant(
        product_id, payload, requester_seller_id=actor.seller_id
    )
    return success_response(data=variant, message="Variant created successfully")


@products_router.patch("/{product_id}/variants/{variant_id}")
async def update_variant(
    product_id: uuid.UUID,
    variant_id: uuid.UUID,
    payload: ProductVariantUpdateRequest,
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductVariantResponse]:
    """Update a variant's sku_code or status. Attribute values are set
    only at creation — to change them, create a new variant. Same
    admin/active-seller access rule as creating a variant."""
    variant = await controller.update_variant(
        product_id, variant_id, payload, requester_seller_id=actor.seller_id
    )
    return success_response(data=variant, message="Variant updated successfully")


# --- images ------------------------------------------------------------------


@products_router.get("/{product_id}/images")
async def list_images(
    product_id: uuid.UUID,
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[list[ProductImageResponse]]:
    """List a product's canonical catalog images."""
    images = await controller.list_images(product_id)
    return success_response(data=images, message="Images retrieved successfully")


@products_router.post("/{product_id}/images", status_code=status.HTTP_201_CREATED)
async def upload_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    is_primary: bool = Form(default=False),
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[ProductImageResponse]:
    """Upload a canonical product image to Cloudinary. Stored publicly
    (unlike seller documents) since buyers browsing the catalog need a
    fast, CDN-cacheable image, not a signed URL. The first image uploaded
    for a product is automatically primary. Same admin/active-seller
    access rule as creating a variant."""
    image = await controller.upload_image(
        product_id,
        file=file,
        is_primary=is_primary,
        requester_seller_id=actor.seller_id,
    )
    return success_response(data=image, message="Image uploaded successfully")


@products_router.delete("/{product_id}/images/{image_id}")
async def delete_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    actor: ProductActor = Depends(require_admin_or_active_seller),
    controller: ProductController = Depends(get_product_controller),
) -> APIResponse[None]:
    """Delete a product image, including its Cloudinary asset. Same
    admin/active-seller access rule as creating a variant."""
    await controller.delete_image(
        product_id, image_id, requester_seller_id=actor.seller_id
    )
    return success_response(message="Image deleted successfully")


# --- seller listings ----------------------------------------------------------


@listings_router.get("")
async def list_my_listings(
    status_filter: str | None = Query(default=None, alias="status"),
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[list[SellerListingResponse]]:
    """List the authenticated seller's listings, optionally filtered by
    status."""
    listings = await controller.list_my_listings(seller.id, status=status_filter)
    return success_response(data=listings, message="Listings retrieved successfully")


@listings_router.get("/{listing_id}")
async def get_listing(
    listing_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Get one listing by id. Ownership is verified in the service layer."""
    listing = await controller.get_listing(seller.id, listing_id)
    return success_response(data=listing, message="Listing retrieved successfully")


@listings_router.post("", status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: SellerListingCreateRequest,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Create a new listing (draft) for an existing variant. The variant
    and its parent product must both be active. Multiple sellers can list
    the same variant, but each seller can only have one listing per
    variant."""
    listing = await controller.create_listing(seller.id, payload)
    return success_response(data=listing, message="Listing created successfully")


@listings_router.patch("/{listing_id}")
async def update_listing(
    listing_id: uuid.UUID,
    payload: SellerListingUpdateRequest,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Update a listing's details (price, stock, seller_sku, condition).
    Only allowed while the listing is in `draft` or `rejected` status."""
    listing = await controller.update_listing(seller.id, listing_id, payload)
    return success_response(data=listing, message="Listing updated successfully")


@listings_router.patch("/{listing_id}/price")
async def update_price(
    listing_id: uuid.UUID,
    payload: SellerListingUpdatePriceRequest,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Update an active listing's price directly."""
    listing = await controller.update_price(seller.id, listing_id, payload)
    return success_response(data=listing, message="Price updated successfully")


@listings_router.patch("/{listing_id}/stock")
async def update_stock(
    listing_id: uuid.UUID,
    payload: SellerListingUpdateStockRequest,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Update an active listing's stock. Setting stock to 0 moves the
    listing to `out_of_stock`."""
    listing = await controller.update_stock(seller.id, listing_id, payload)
    return success_response(data=listing, message="Stock updated successfully")


@listings_router.post("/{listing_id}/submit")
async def submit_listing_for_review(
    listing_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Submit a `draft` or `rejected` listing for admin review."""
    listing = await controller.submit_for_review(seller.id, listing_id)
    return success_response(data=listing, message="Listing submitted for review")


@listings_router.post("/{listing_id}/approve")
async def approve_listing(
    listing_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Approve a `pending_review` listing, moving it to `active`. Admin
    only."""
    listing = await controller.approve(listing_id)
    return success_response(data=listing, message="Listing approved successfully")


@listings_router.post("/{listing_id}/reject")
async def reject_listing(
    listing_id: uuid.UUID,
    payload: RejectListingRequest,
    admin: Account = Depends(require_role("admin")),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Reject a `pending_review` listing with a reason. Admin only."""
    listing = await controller.reject(listing_id, payload)
    return success_response(data=listing, message="Listing rejected")


@listings_router.post("/{listing_id}/suspend")
async def suspend_listing(
    listing_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Suspend an `active` listing. Admin only."""
    listing = await controller.suspend(listing_id)
    return success_response(data=listing, message="Listing suspended")


@listings_router.post("/{listing_id}/reactivate")
async def reactivate_listing(
    listing_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Reactivate a `suspended` listing. Admin only."""
    listing = await controller.reactivate(listing_id)
    return success_response(data=listing, message="Listing reactivated")


@listings_router.post("/{listing_id}/archive")
async def archive_listing(
    listing_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Archive an `active` listing, hiding it from buyers without
    deleting it."""
    listing = await controller.archive(seller.id, listing_id)
    return success_response(data=listing, message="Listing archived")


@listings_router.post("/{listing_id}/unarchive")
async def unarchive_listing(
    listing_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[SellerListingResponse]:
    """Unarchive an `archived` listing, making it active again."""
    listing = await controller.unarchive(seller.id, listing_id)
    return success_response(data=listing, message="Listing unarchived")


@listings_router.delete("/{listing_id}")
async def delete_listing(
    listing_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[None]:
    """Delete a `draft` listing permanently. Only draft listings can be
    deleted."""
    await controller.delete_listing(seller.id, listing_id)
    return success_response(message="Listing deleted successfully")


# --- listing images -----------------------------------------------------------


@listings_router.get("/{listing_id}/images")
async def list_listing_images(
    listing_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[list[ListingImageResponse]]:
    """List a listing's images."""
    images = await controller.list_images(listing_id)
    return success_response(data=images, message="Images retrieved successfully")


@listings_router.post("/{listing_id}/images", status_code=status.HTTP_201_CREATED)
async def upload_listing_image(
    listing_id: uuid.UUID,
    file: UploadFile = File(...),
    is_primary: bool = Form(default=False),
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[ListingImageResponse]:
    """Upload an image for a listing to Cloudinary. Only the listing's
    owning seller can do this."""
    image = await controller.upload_image(
        seller.id, listing_id, file=file, is_primary=is_primary
    )
    return success_response(data=image, message="Image uploaded successfully")


@listings_router.delete("/{listing_id}/images/{image_id}")
async def delete_listing_image(
    listing_id: uuid.UUID,
    image_id: uuid.UUID,
    seller: Account = Depends(get_current_account),
    controller: ListingController = Depends(get_listing_controller),
) -> APIResponse[None]:
    """Delete a listing image, including its Cloudinary asset. Only the
    listing's owning seller can do this."""
    await controller.delete_image(seller.id, listing_id, image_id)
    return success_response(message="Image deleted successfully")
