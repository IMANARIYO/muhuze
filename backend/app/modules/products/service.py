import uuid

from fastapi import UploadFile

from app.core import storage
from app.modules.categories.repository import CategoryRepository
from app.modules.products.exceptions import (
    AttributeNotFoundError,
    BrandNameAlreadyTakenError,
    BrandNotFoundError,
    DuplicateSellerListingError,
    DuplicateVariantAttributeError,
    DuplicateVariantAttributesError,
    ListingNotApprovableError,
    ListingNotArchivableError,
    ListingNotDeletableError,
    ListingNotEditableError,
    ListingNotReactivatableError,
    ListingNotSubmittableError,
    ListingNotSuspendableError,
    ListingNotUnarchivableError,
    ListingPriceUpdateOnNonActiveError,
    ListingStockUpdateOnNonActiveError,
    ProductBrandNotFoundError,
    ProductCategoryNotFoundError,
    ProductImageNotFoundError,
    ProductNotActiveError,
    ProductNotArchivableError,
    ProductNotEditableError,
    ProductNotFoundError,
    ProductNotPendingReviewError,
    ProductNotSubmittableError,
    ProductOwnershipError,
    ProductVariantNotFoundError,
    SellerListingImageNotFoundError,
    SellerListingNotFoundError,
    SellerNotActiveError,
    SellerOwnershipError,
    VariantNotActiveError,
)
from app.modules.products.models import (
    Attribute,
    Brand,
    ListingImage,
    ListingStatus,
    Product,
    ProductImage,
    ProductStatus,
    ProductVariant,
    SellerListing,
    VariantAttributeValue,
)
from app.modules.products.repository import (
    AttributeRepository,
    BrandRepository,
    ListingImageRepository,
    ProductImageRepository,
    ProductRepository,
    ProductVariantRepository,
    SellerListingRepository,
)
from app.modules.sellers.repository import SellerRepository
from app.shared.utils.slugify import slugify

PRODUCT_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PRODUCT_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _default_attributes() -> list[Attribute]:
    """Seed data — the shared, admin-curated vocabulary sellers pick from
    when adding variant attribute values (Color=Black, Storage=256GB, ...).
    Mirrors the categories/brands seeded via the admin "Catalog setup" UI."""
    definition = [
        ("Color", "Color", "select", None),
        ("Size", "Size", "select", None),
        ("RAM", "RAM", "select", "GB"),
        ("Storage", "Storage", "select", "GB"),
        ("Material", "Material", "select", None),
        ("Version", "Version", "select", None),
        ("Weight", "Weight", "number", "kg"),
    ]
    return [
        Attribute(
            name=name,
            slug=slug,
            input_type=input_type,
            unit=unit,
        )
        for name, slug, input_type, unit in definition
    ]


async def seed_default_attributes(repository: AttributeRepository) -> int:
    """Idempotent: creates the default attributes if their slugs don't yet
    exist. Never overwrites an admin's existing / edited attributes. Returns
    how many attributes were created. Called at app startup — see
    app/core/bootstrap.py."""
    created = 0
    for attribute in _default_attributes():
        if await repository.get_by_slug(attribute.slug) is None:
            await repository.create(
                name=attribute.name,
                slug=attribute.slug,
                input_type=attribute.input_type,
                unit=attribute.unit,
            )
            created += 1
    return created


def _check_product_write_access(
    product: Product, requester_seller_id: uuid.UUID | None
) -> None:
    """Shared by ProductVariantService and ProductImageService — both
    extend the same product, under the same rule. `requester_seller_id
    =None` means admin, always allowed. Otherwise: once the product is
    `active` it's shared catalog, so any active seller may add to it
    (that's what makes "many sellers, same product" real for variants
    nobody's requested yet); before that, only the seller who requested
    it may touch it — it isn't part of the real catalog yet."""
    if requester_seller_id is None:
        return
    if product.status == ProductStatus.ACTIVE:
        return
    if product.created_by_seller_id != requester_seller_id:
        raise ProductOwnershipError()


class BrandService:
    """Business rules for brands. Slug generation/uniqueness lives here,
    not in the repository — same pattern as CategoryService."""

    def __init__(self, brands: BrandRepository) -> None:
        self.brands = brands

    async def get_by_id(self, brand_id: uuid.UUID) -> Brand:
        brand = await self.brands.get_by_id(brand_id)
        if brand is None:
            raise BrandNotFoundError()
        return brand

    async def list_all(self) -> list[Brand]:
        return await self.brands.list_all()

    async def create(self, *, name: str, description: str | None) -> Brand:
        if await self.brands.get_by_name(name) is not None:
            raise BrandNameAlreadyTakenError()
        slug = await self._unique_slug(name)
        return await self.brands.create(name=name, slug=slug, description=description)

    async def update(
        self, brand_id: uuid.UUID, *, name: str, description: str | None, status: str
    ) -> Brand:
        brand = await self.get_by_id(brand_id)
        if name != brand.name:
            holder = await self.brands.get_by_name(name)
            if holder is not None and holder.id != brand.id:
                raise BrandNameAlreadyTakenError()
        return await self.brands.update(
            brand, name=name, description=description, status=status
        )

    async def _unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while await self.brands.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug


class AttributeService:
    """Business rules for attributes (the global vocabulary sellers pick
    from when defining variants — Color, RAM, Size, etc.)."""

    def __init__(self, attributes: AttributeRepository) -> None:
        self.attributes = attributes

    async def get_by_id(self, attribute_id: uuid.UUID) -> Attribute:
        attribute = await self.attributes.get_by_id(attribute_id)
        if attribute is None:
            raise AttributeNotFoundError()
        return attribute

    async def list_all(self) -> list[Attribute]:
        return await self.attributes.list_all()

    async def create(
        self, *, name: str, input_type: str, unit: str | None
    ) -> Attribute:
        slug = await self._unique_slug(name)
        return await self.attributes.create(
            name=name, slug=slug, input_type=input_type, unit=unit
        )

    async def update(
        self,
        attribute_id: uuid.UUID,
        *,
        name: str,
        input_type: str,
        unit: str | None,
        status: str,
    ) -> Attribute:
        attribute = await self.get_by_id(attribute_id)
        return await self.attributes.update(
            attribute, name=name, input_type=input_type, unit=unit, status=status
        )

    async def _unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while await self.attributes.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug


class ProductService:
    """Business rules for the product (SPU) lifecycle. The catalog is
    still admin-approved end to end, but creation is no longer
    admin-only: an active seller can request a new product (tagged via
    created_by_seller_id) the same way admin can create one directly
    (created_by_seller_id left null). While a product is
    draft/pending_review/rejected, only its requesting seller (or admin)
    may touch it — see `_check_owner`. Once active, ownership stops
    gating anything: any active seller can extend the shared catalog
    with new variants/images — see ProductVariantService/
    ProductImageService. Admin remains the only approve/reject/archive
    gate. See products/docs/product-lifecycle.md."""

    def __init__(
        self,
        products: ProductRepository,
        categories: CategoryRepository,
        brands: BrandRepository,
    ) -> None:
        self.products = products
        self.categories = categories
        self.brands = brands

    async def get_by_id(self, product_id: uuid.UUID) -> Product:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError()
        return product

    async def list_all(
        self,
        *,
        category_id: uuid.UUID | None,
        brand_id: uuid.UUID | None,
        status: str | None,
        search: str | None = None,
    ) -> list[Product]:
        return await self.products.list_all(
            category_id=category_id, brand_id=brand_id, status=status, search=search
        )

    async def list_mine(self, seller_id: uuid.UUID) -> list[Product]:
        return await self.products.list_by_seller(seller_id)

    async def create(
        self,
        *,
        category_id: uuid.UUID,
        brand_id: uuid.UUID | None,
        name: str,
        description: str | None,
        created_by_seller_id: uuid.UUID | None = None,
    ) -> Product:
        await self._validate_references(category_id, brand_id)
        slug = await self._unique_slug(name)
        return await self.products.create(
            category_id=category_id,
            brand_id=brand_id,
            name=name,
            slug=slug,
            description=description,
            created_by_seller_id=created_by_seller_id,
        )

    async def update(
        self,
        product_id: uuid.UUID,
        *,
        category_id: uuid.UUID,
        brand_id: uuid.UUID | None,
        name: str,
        description: str | None,
        requester_seller_id: uuid.UUID | None = None,
    ) -> Product:
        product = await self.get_by_id(product_id)
        self._check_owner(product, requester_seller_id)
        if product.status not in (ProductStatus.DRAFT, ProductStatus.REJECTED):
            raise ProductNotEditableError()
        await self._validate_references(category_id, brand_id)
        return await self.products.update_details(
            product,
            category_id=category_id,
            brand_id=brand_id,
            name=name,
            description=description,
        )

    async def submit_for_review(
        self, product_id: uuid.UUID, *, requester_seller_id: uuid.UUID | None = None
    ) -> Product:
        product = await self.get_by_id(product_id)
        self._check_owner(product, requester_seller_id)
        if product.status not in (ProductStatus.DRAFT, ProductStatus.REJECTED):
            raise ProductNotSubmittableError()
        return await self.products.update_status(
            product, status=ProductStatus.PENDING_REVIEW
        )

    async def approve(self, product_id: uuid.UUID) -> Product:
        product = await self.get_by_id(product_id)
        if product.status != ProductStatus.PENDING_REVIEW:
            raise ProductNotPendingReviewError()
        return await self.products.update_status(product, status=ProductStatus.ACTIVE)

    async def reject(self, product_id: uuid.UUID, *, reason: str) -> Product:
        product = await self.get_by_id(product_id)
        if product.status != ProductStatus.PENDING_REVIEW:
            raise ProductNotPendingReviewError()
        return await self.products.update_status(
            product, status=ProductStatus.REJECTED, rejection_reason=reason
        )

    async def archive(self, product_id: uuid.UUID) -> Product:
        product = await self.get_by_id(product_id)
        if product.status != ProductStatus.ACTIVE:
            raise ProductNotArchivableError()
        return await self.products.update_status(product, status=ProductStatus.ARCHIVED)

    def _check_owner(
        self, product: Product, requester_seller_id: uuid.UUID | None
    ) -> None:
        """`requester_seller_id=None` means the caller is admin — no
        check. Otherwise the caller must be the seller who requested this
        product. Only meaningful while draft/pending_review/rejected —
        callers don't call this at all for the active-product case (see
        class docstring)."""
        if (
            requester_seller_id is not None
            and product.created_by_seller_id != requester_seller_id
        ):
            raise ProductOwnershipError()

    async def _validate_references(
        self, category_id: uuid.UUID, brand_id: uuid.UUID | None
    ) -> None:
        if await self.categories.get_by_id(category_id) is None:
            raise ProductCategoryNotFoundError()
        if brand_id is not None and await self.brands.get_by_id(brand_id) is None:
            raise ProductBrandNotFoundError()

    async def _unique_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while await self.products.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug


class ProductVariantService:
    """Business rules for product variants (SKUs). Enforces that no two
    variants of the same product share the exact same combination of
    attribute values — see products/docs/attributes-and-variants.md.
    Category-scoped attribute rules (required/variant/filterable) are
    deliberately NOT enforced yet — CategoryAttribute exists as a table
    but has no service built on it in this phase."""

    def __init__(
        self,
        variants: ProductVariantRepository,
        products: ProductRepository,
        attributes: AttributeRepository,
    ) -> None:
        self.variants = variants
        self.products = products
        self.attributes = attributes

    async def get_by_id(self, variant_id: uuid.UUID) -> ProductVariant:
        variant = await self.variants.get_by_id(variant_id)
        if variant is None:
            raise ProductVariantNotFoundError()
        return variant

    async def list_by_product(
        self, product_id: uuid.UUID
    ) -> list[tuple[ProductVariant, list[VariantAttributeValue]]]:
        if await self.products.get_by_id(product_id) is None:
            raise ProductNotFoundError()
        product_variants = await self.variants.list_by_product(product_id)
        values = await self.variants.list_attribute_values_for_variants(
            [variant.id for variant in product_variants]
        )
        by_variant: dict[uuid.UUID, list[VariantAttributeValue]] = {
            variant.id: [] for variant in product_variants
        }
        for value in values:
            by_variant[value.variant_id].append(value)
        return [(variant, by_variant[variant.id]) for variant in product_variants]

    async def create(
        self,
        product_id: uuid.UUID,
        *,
        sku_code: str | None,
        attribute_values: list[tuple[uuid.UUID, str]],
        requester_seller_id: uuid.UUID | None = None,
    ) -> tuple[ProductVariant, list[VariantAttributeValue]]:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError()
        _check_product_write_access(product, requester_seller_id)

        seen_attribute_ids: set[uuid.UUID] = set()
        for attribute_id, _value in attribute_values:
            if attribute_id in seen_attribute_ids:
                raise DuplicateVariantAttributeError()
            seen_attribute_ids.add(attribute_id)
            if await self.attributes.get_by_id(attribute_id) is None:
                raise AttributeNotFoundError()

        await self._check_unique_combination(
            product_id, attribute_values, exclude_variant_id=None
        )

        variant = await self.variants.create(product_id=product_id, sku_code=sku_code)
        for attribute_id, value in attribute_values:
            await self.variants.add_attribute_value(
                variant_id=variant.id, attribute_id=attribute_id, value=value
            )
        values = await self.variants.list_attribute_values(variant.id)
        return variant, values

    async def update(
        self,
        variant_id: uuid.UUID,
        *,
        sku_code: str | None,
        status: str,
        requester_seller_id: uuid.UUID | None = None,
    ) -> ProductVariant:
        variant = await self.get_by_id(variant_id)
        product = await self.products.get_by_id(variant.product_id)
        if product is None:
            raise ProductNotFoundError()
        _check_product_write_access(product, requester_seller_id)
        return await self.variants.update(variant, sku_code=sku_code, status=status)

    async def list_attribute_values(
        self, variant_id: uuid.UUID
    ) -> list[VariantAttributeValue]:
        return await self.variants.list_attribute_values(variant_id)

    async def _check_unique_combination(
        self,
        product_id: uuid.UUID,
        attribute_values: list[tuple[uuid.UUID, str]],
        *,
        exclude_variant_id: uuid.UUID | None,
    ) -> None:
        candidate = frozenset(attribute_values)
        existing_variants = await self.variants.list_by_product(product_id)
        existing_values = await self.variants.list_attribute_values_for_variants(
            [v.id for v in existing_variants if v.id != exclude_variant_id]
        )
        by_variant: dict[uuid.UUID, set[tuple[uuid.UUID, str]]] = {}
        for value in existing_values:
            by_variant.setdefault(value.variant_id, set()).add(
                (value.attribute_id, value.value)
            )
        for combination in by_variant.values():
            if frozenset(combination) == candidate:
                raise DuplicateVariantAttributesError()


class ProductImageService:
    """Business rules for canonical product images. Uses
    delivery_type='upload' (public, CDN-cacheable) — unlike seller
    documents, these are meant to be shown to any buyer browsing the
    catalog, so 'authenticated'/signed URLs would be the wrong pattern
    here."""

    def __init__(
        self, images: ProductImageRepository, products: ProductRepository
    ) -> None:
        self.images = images
        self.products = products

    async def list_by_product(self, product_id: uuid.UUID) -> list[ProductImage]:
        if await self.products.get_by_id(product_id) is None:
            raise ProductNotFoundError()
        return await self.images.list_by_product(product_id)

    async def upload(
        self,
        product_id: uuid.UUID,
        *,
        file: UploadFile,
        is_primary: bool,
        requester_seller_id: uuid.UUID | None = None,
    ) -> ProductImage:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError()
        _check_product_write_access(product, requester_seller_id)

        uploaded = await storage.upload_file(
            file,
            folder="products",
            allowed_content_types=PRODUCT_IMAGE_CONTENT_TYPES,
            max_size_bytes=MAX_PRODUCT_IMAGE_SIZE_BYTES,
            delivery_type="upload",
        )
        existing = await self.images.list_by_product(product_id)
        return await self.images.create(
            product_id=product_id,
            cloudinary_public_id=uploaded.public_id,
            cloudinary_resource_type=uploaded.resource_type,
            original_filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            file_size=uploaded.bytes,
            sort_order=len(existing),
            is_primary=is_primary or not existing,
        )

    async def delete(
        self,
        product_id: uuid.UUID,
        image_id: uuid.UUID,
        *,
        requester_seller_id: uuid.UUID | None = None,
    ) -> None:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError()
        _check_product_write_access(product, requester_seller_id)
        image = await self.images.get_by_id(image_id)
        if image is None or image.product_id != product_id:
            raise ProductImageNotFoundError()
        await self.images.delete(image)
        await storage.delete_file(
            image.cloudinary_public_id,
            resource_type=image.cloudinary_resource_type,
            delivery_type="upload",
        )


LISTING_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_LISTING_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class SellerListingService:
    """Business rules for seller listings. Sellers create offers for
    existing variants — they don't create products or variants themselves.
    The listing lifecycle: draft → pending_review → active →
    rejected/suspended/out_of_stock/archived — see
    products/docs/seller-listing-flow.md."""

    def __init__(
        self,
        listings: SellerListingRepository,
        sellers: SellerRepository,
        variants: ProductVariantRepository,
        products: ProductRepository,
    ) -> None:
        self.listings = listings
        self.sellers = sellers
        self.variants = variants
        self.products = products

    async def _get_seller_by_account(self, account_id: uuid.UUID):
        from app.modules.sellers.exceptions import SellerNotFoundError as _SNE

        seller = await self.sellers.get_by_account_id(account_id)
        if seller is None:
            raise _SNE()
        return seller

    async def _ensure_active_seller(self, account_id: uuid.UUID):
        seller = await self._get_seller_by_account(account_id)
        if seller.status != "active":
            raise SellerNotActiveError()
        return seller

    async def get_by_id(self, listing_id: uuid.UUID) -> SellerListing:
        listing = await self.listings.get_by_id(listing_id)
        if listing is None:
            raise SellerListingNotFoundError()
        return listing

    async def get_owned(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListing:
        """Resolve the caller's own Seller row and verify it owns this
        listing. `listing.seller_id` is a Seller.id (business profile),
        never the same UUID space as Account.id — every "does the caller
        own this listing" check must go through this, not a direct
        `listing.seller_id != account_id` comparison, which can never be
        true and would silently 403 the real owner."""
        seller = await self._ensure_active_seller(account_id)
        listing = await self.get_by_id(listing_id)
        if listing.seller_id != seller.id:
            raise SellerOwnershipError()
        return listing

    async def list_by_seller(
        self, account_id: uuid.UUID, status: str | None
    ) -> list[SellerListing]:
        seller = await self._ensure_active_seller(account_id)
        return await self.listings.list_by_seller(seller.id, status=status)

    async def list_all(self, status: str | None) -> list[SellerListing]:
        """Admin review: every listing across all sellers, optionally
        filtered by status (e.g. `pending_review`)."""
        return await self.listings.list_all(status=status)

    async def create(
        self,
        account_id: uuid.UUID,
        *,
        variant_id: uuid.UUID,
        price: float,
        stock: int,
        seller_sku: str | None,
        condition: str,
    ) -> SellerListing:
        seller = await self._ensure_active_seller(account_id)

        variant = await self.variants.get_by_id(variant_id)
        if variant is None:
            raise ProductVariantNotFoundError()
        if variant.status != "active":
            raise VariantNotActiveError()

        product = await self.products.get_by_id(variant.product_id)
        if product is None or product.status != "active":
            raise ProductNotActiveError()

        existing = await self.listings.list_by_seller(seller.id, status=None)
        for e in existing:
            if e.variant_id == variant_id:
                raise DuplicateSellerListingError()

        return await self.listings.create(
            seller_id=seller.id,
            variant_id=variant_id,
            price=price,
            stock=stock,
            seller_sku=seller_sku,
            condition=condition,
        )

    async def update_details(
        self,
        account_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        price: float,
        stock: int,
        seller_sku: str | None,
        condition: str,
    ) -> SellerListing:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status not in (ListingStatus.DRAFT, ListingStatus.REJECTED):
            raise ListingNotEditableError()
        return await self.listings.update_details(
            listing,
            price=price,
            stock=stock,
            seller_sku=seller_sku,
            condition=condition,
        )

    async def update_price(
        self, account_id: uuid.UUID, listing_id: uuid.UUID, *, price: float
    ) -> SellerListing:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status != ListingStatus.ACTIVE:
            raise ListingPriceUpdateOnNonActiveError()
        return await self.listings.update_price(listing, price=price)

    async def update_stock(
        self, account_id: uuid.UUID, listing_id: uuid.UUID, *, stock: int
    ) -> SellerListing:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status != ListingStatus.ACTIVE:
            raise ListingStockUpdateOnNonActiveError()
        if stock == 0:
            return await self.listings.update_status(
                listing, status=ListingStatus.OUT_OF_STOCK
            )
        return await self.listings.update_stock(listing, stock=stock)

    async def submit_for_review(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListing:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status not in (ListingStatus.DRAFT, ListingStatus.REJECTED):
            raise ListingNotSubmittableError()
        return await self.listings.update_status(
            listing, status=ListingStatus.PENDING_REVIEW
        )

    async def approve(self, listing_id: uuid.UUID) -> SellerListing:
        listing = await self.get_by_id(listing_id)
        if listing.status != ListingStatus.PENDING_REVIEW:
            raise ListingNotApprovableError()
        return await self.listings.update_status(listing, status=ListingStatus.ACTIVE)

    async def reject(self, listing_id: uuid.UUID, *, reason: str) -> SellerListing:
        listing = await self.get_by_id(listing_id)
        if listing.status != ListingStatus.PENDING_REVIEW:
            raise ListingNotApprovableError()
        return await self.listings.update_status(
            listing, status=ListingStatus.REJECTED, rejection_reason=reason
        )

    async def suspend(self, listing_id: uuid.UUID) -> SellerListing:
        listing = await self.get_by_id(listing_id)
        if listing.status != ListingStatus.ACTIVE:
            raise ListingNotSuspendableError()
        return await self.listings.update_status(
            listing, status=ListingStatus.SUSPENDED
        )

    async def reactivate(self, listing_id: uuid.UUID) -> SellerListing:
        listing = await self.get_by_id(listing_id)
        if listing.status != ListingStatus.SUSPENDED:
            raise ListingNotReactivatableError()
        return await self.listings.update_status(listing, status=ListingStatus.ACTIVE)

    async def archive(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListing:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status != ListingStatus.ACTIVE:
            raise ListingNotArchivableError()
        return await self.listings.update_status(listing, status=ListingStatus.ARCHIVED)

    async def unarchive(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListing:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status != ListingStatus.ARCHIVED:
            raise ListingNotUnarchivableError()
        return await self.listings.update_status(listing, status=ListingStatus.ACTIVE)

    async def delete(self, account_id: uuid.UUID, listing_id: uuid.UUID) -> None:
        listing = await self.get_owned(account_id, listing_id)
        if listing.status != ListingStatus.DRAFT:
            raise ListingNotDeletableError()
        await self.listings.delete(listing)


class ListingImageService:
    """Business rules for listing images. Uses delivery_type='upload'
    (public, CDN-cacheable) — same pattern as ProductImageService.
    Reading is intentionally open to anyone (a buyer deciding whether to
    buy from this seller needs to see these photos without logging in) —
    only upload/delete are seller-owner-only, enforced via
    `SellerListingService.get_owned`."""

    def __init__(
        self,
        images: ListingImageRepository,
        listings: SellerListingService,
    ) -> None:
        self.images = images
        self.listings = listings

    async def list_by_listing(self, listing_id: uuid.UUID) -> list[ListingImage]:
        await self.listings.get_by_id(listing_id)
        return await self.images.list_by_listing(listing_id)

    async def upload(
        self,
        account_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        file: UploadFile,
        is_primary: bool,
    ) -> ListingImage:
        await self.listings.get_owned(account_id, listing_id)

        uploaded = await storage.upload_file(
            file,
            folder="listing-images",
            allowed_content_types=LISTING_IMAGE_CONTENT_TYPES,
            max_size_bytes=MAX_LISTING_IMAGE_SIZE_BYTES,
            delivery_type="upload",
        )
        existing = await self.images.list_by_listing(listing_id)
        return await self.images.create(
            listing_id=listing_id,
            cloudinary_public_id=uploaded.public_id,
            cloudinary_resource_type=uploaded.resource_type,
            original_filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            file_size=uploaded.bytes,
            sort_order=len(existing),
            is_primary=is_primary or not existing,
        )

    async def delete(
        self, account_id: uuid.UUID, listing_id: uuid.UUID, image_id: uuid.UUID
    ) -> None:
        await self.listings.get_owned(account_id, listing_id)
        image = await self.images.get_by_id(image_id)
        if image is None or image.listing_id != listing_id:
            raise SellerListingImageNotFoundError()
        await self.images.delete(image)
        await storage.delete_file(
            image.cloudinary_public_id,
            resource_type=image.cloudinary_resource_type,
            delivery_type="upload",
        )
