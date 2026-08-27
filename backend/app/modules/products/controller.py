import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.categories.repository import CategoryRepository
from app.modules.products.exceptions import ProductVariantNotFoundError
from app.modules.products.models import (
    ListingImage,
    ProductImage,
    ProductVariant,
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
    VariantAttributeValueResponse,
)
from app.modules.products.service import (
    AttributeService,
    BrandService,
    ListingImageService,
    ProductImageService,
    ProductService,
    ProductVariantService,
    SellerListingService,
)
from app.modules.sellers.repository import SellerRepository


class BrandController:
    """Translates HTTP requests/responses to and from the brand service."""

    def __init__(self, db: AsyncSession) -> None:
        self.brands = BrandService(BrandRepository(db))

    async def get_brand(self, brand_id: uuid.UUID) -> BrandResponse:
        brand = await self.brands.get_by_id(brand_id)
        return BrandResponse.model_validate(brand)

    async def list_brands(self) -> list[BrandResponse]:
        brands = await self.brands.list_all()
        return [BrandResponse.model_validate(brand) for brand in brands]

    async def create_brand(self, payload: BrandCreateRequest) -> BrandResponse:
        brand = await self.brands.create(
            name=payload.name, description=payload.description
        )
        return BrandResponse.model_validate(brand)

    async def update_brand(
        self, brand_id: uuid.UUID, payload: BrandUpdateRequest
    ) -> BrandResponse:
        brand = await self.brands.update(
            brand_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
        )
        return BrandResponse.model_validate(brand)


class AttributeController:
    """Translates HTTP requests/responses to and from the attribute service."""

    def __init__(self, db: AsyncSession) -> None:
        self.attributes = AttributeService(AttributeRepository(db))

    async def get_attribute(self, attribute_id: uuid.UUID) -> AttributeResponse:
        attribute = await self.attributes.get_by_id(attribute_id)
        return AttributeResponse.model_validate(attribute)

    async def list_attributes(self) -> list[AttributeResponse]:
        attributes = await self.attributes.list_all()
        return [AttributeResponse.model_validate(attribute) for attribute in attributes]

    async def create_attribute(
        self, payload: AttributeCreateRequest
    ) -> AttributeResponse:
        attribute = await self.attributes.create(
            name=payload.name, input_type=payload.input_type, unit=payload.unit
        )
        return AttributeResponse.model_validate(attribute)

    async def update_attribute(
        self, attribute_id: uuid.UUID, payload: AttributeUpdateRequest
    ) -> AttributeResponse:
        attribute = await self.attributes.update(
            attribute_id,
            name=payload.name,
            input_type=payload.input_type,
            unit=payload.unit,
            status=payload.status,
        )
        return AttributeResponse.model_validate(attribute)


class ProductController:
    """Translates HTTP requests/responses to and from the product,
    variant, and image services. Kept as one controller since variants and
    images are always reached through a product (/products/{id}/...)."""

    def __init__(self, db: AsyncSession) -> None:
        products = ProductRepository(db)
        attributes = AttributeRepository(db)
        self.products = ProductService(
            products, CategoryRepository(db), BrandRepository(db)
        )
        self.variants = ProductVariantService(
            ProductVariantRepository(db), products, attributes
        )
        self.images = ProductImageService(ProductImageRepository(db), products)

    # --- products -----------------------------------------------------

    async def get_product(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self.products.get_by_id(product_id)
        return ProductResponse.model_validate(product)

    async def list_products(
        self,
        *,
        category_id: uuid.UUID | None,
        brand_id: uuid.UUID | None,
        status: str | None,
    ) -> list[ProductResponse]:
        products = await self.products.list_all(
            category_id=category_id, brand_id=brand_id, status=status
        )
        return [ProductResponse.model_validate(product) for product in products]

    async def create_product(self, payload: ProductCreateRequest) -> ProductResponse:
        product = await self.products.create(
            category_id=payload.category_id,
            brand_id=payload.brand_id,
            name=payload.name,
            description=payload.description,
        )
        return ProductResponse.model_validate(product)

    async def update_product(
        self, product_id: uuid.UUID, payload: ProductUpdateRequest
    ) -> ProductResponse:
        product = await self.products.update(
            product_id,
            category_id=payload.category_id,
            brand_id=payload.brand_id,
            name=payload.name,
            description=payload.description,
        )
        return ProductResponse.model_validate(product)

    async def submit_for_review(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self.products.submit_for_review(product_id)
        return ProductResponse.model_validate(product)

    async def approve(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self.products.approve(product_id)
        return ProductResponse.model_validate(product)

    async def reject(
        self, product_id: uuid.UUID, payload: RejectProductRequest
    ) -> ProductResponse:
        product = await self.products.reject(product_id, reason=payload.reason)
        return ProductResponse.model_validate(product)

    async def archive(self, product_id: uuid.UUID) -> ProductResponse:
        product = await self.products.archive(product_id)
        return ProductResponse.model_validate(product)

    # --- variants -------------------------------------------------------

    async def list_variants(
        self, product_id: uuid.UUID
    ) -> list[ProductVariantResponse]:
        pairs = await self.variants.list_by_product(product_id)
        return [self._to_variant_response(variant, values) for variant, values in pairs]

    async def create_variant(
        self, product_id: uuid.UUID, payload: ProductVariantCreateRequest
    ) -> ProductVariantResponse:
        variant, values = await self.variants.create(
            product_id,
            sku_code=payload.sku_code,
            attribute_values=[
                (item.attribute_id, item.value) for item in payload.attribute_values
            ],
        )
        return self._to_variant_response(variant, values)

    async def update_variant(
        self,
        product_id: uuid.UUID,
        variant_id: uuid.UUID,
        payload: ProductVariantUpdateRequest,
    ) -> ProductVariantResponse:
        existing = await self.variants.get_by_id(variant_id)
        if existing.product_id != product_id:
            raise ProductVariantNotFoundError()
        variant = await self.variants.update(
            variant_id, sku_code=payload.sku_code, status=payload.status
        )
        values = await self.variants.list_attribute_values(variant.id)
        return self._to_variant_response(variant, values)

    # --- images -----------------------------------------------------------

    async def list_images(self, product_id: uuid.UUID) -> list[ProductImageResponse]:
        images = await self.images.list_by_product(product_id)
        return [await self._to_image_response(image) for image in images]

    async def upload_image(
        self, product_id: uuid.UUID, *, file: UploadFile, is_primary: bool
    ) -> ProductImageResponse:
        image = await self.images.upload(product_id, file=file, is_primary=is_primary)
        return await self._to_image_response(image)

    async def delete_image(self, product_id: uuid.UUID, image_id: uuid.UUID) -> None:
        await self.images.delete(product_id, image_id)

    # --- shared -----------------------------------------------------------

    def _to_variant_response(
        self, variant: ProductVariant, values: list[VariantAttributeValue]
    ) -> ProductVariantResponse:
        return ProductVariantResponse(
            id=variant.id,
            product_id=variant.product_id,
            sku_code=variant.sku_code,
            status=variant.status,
            attribute_values=[
                VariantAttributeValueResponse.model_validate(value) for value in values
            ],
            created_at=variant.created_at,
            updated_at=variant.updated_at,
        )

    async def _to_image_response(self, image: ProductImage) -> ProductImageResponse:
        url = await storage.get_public_url(
            image.cloudinary_public_id, resource_type=image.cloudinary_resource_type
        )
        return ProductImageResponse(
            id=image.id,
            product_id=image.product_id,
            url=url,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            created_at=image.created_at,
        )


class ListingController:
    """Translates HTTP requests/responses to and from the seller listing
    and listing image services. Kept as one controller since listing
    images are always reached through a listing (/listings/{id}/images)."""

    def __init__(self, db: AsyncSession) -> None:
        self.listings = SellerListingService(
            SellerListingRepository(db),
            SellerRepository(db),
            ProductVariantRepository(db),
            ProductRepository(db),
        )
        self.images = ListingImageService(ListingImageRepository(db), self.listings)

    async def list_my_listings(
        self, account_id: uuid.UUID, status: str | None
    ) -> list[SellerListingResponse]:
        listings = await self.listings.list_by_seller(account_id, status=status)
        return [SellerListingResponse.model_validate(l) for l in listings]

    async def get_listing(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListingResponse:
        listing = await self.listings.get_owned(account_id, listing_id)
        return SellerListingResponse.model_validate(listing)

    async def create_listing(
        self, account_id: uuid.UUID, payload: SellerListingCreateRequest
    ) -> SellerListingResponse:
        listing = await self.listings.create(
            account_id,
            variant_id=payload.variant_id,
            price=payload.price,
            stock=payload.stock,
            seller_sku=payload.seller_sku,
            condition=payload.condition,
        )
        return SellerListingResponse.model_validate(listing)

    async def update_listing(
        self,
        account_id: uuid.UUID,
        listing_id: uuid.UUID,
        payload: SellerListingUpdateRequest,
    ) -> SellerListingResponse:
        current = await self.listings.get_by_id(listing_id)
        listing = await self.listings.update_details(
            account_id,
            listing_id,
            price=payload.price if payload.price is not None else current.price,
            stock=payload.stock if payload.stock is not None else current.stock,
            seller_sku=payload.seller_sku
            if payload.seller_sku is not None
            else current.seller_sku,
            condition=payload.condition
            if payload.condition is not None
            else current.condition,
        )
        return SellerListingResponse.model_validate(listing)

    async def update_price(
        self,
        account_id: uuid.UUID,
        listing_id: uuid.UUID,
        payload: SellerListingUpdatePriceRequest,
    ) -> SellerListingResponse:
        listing = await self.listings.update_price(
            account_id, listing_id, price=payload.price
        )
        return SellerListingResponse.model_validate(listing)

    async def update_stock(
        self,
        account_id: uuid.UUID,
        listing_id: uuid.UUID,
        payload: SellerListingUpdateStockRequest,
    ) -> SellerListingResponse:
        listing = await self.listings.update_stock(
            account_id, listing_id, stock=payload.stock
        )
        return SellerListingResponse.model_validate(listing)

    async def submit_for_review(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListingResponse:
        listing = await self.listings.submit_for_review(account_id, listing_id)
        return SellerListingResponse.model_validate(listing)

    async def approve(self, listing_id: uuid.UUID) -> SellerListingResponse:
        listing = await self.listings.approve(listing_id)
        return SellerListingResponse.model_validate(listing)

    async def reject(
        self, listing_id: uuid.UUID, payload: RejectListingRequest
    ) -> SellerListingResponse:
        listing = await self.listings.reject(listing_id, reason=payload.reason)
        return SellerListingResponse.model_validate(listing)

    async def suspend(self, listing_id: uuid.UUID) -> SellerListingResponse:
        listing = await self.listings.suspend(listing_id)
        return SellerListingResponse.model_validate(listing)

    async def reactivate(self, listing_id: uuid.UUID) -> SellerListingResponse:
        listing = await self.listings.reactivate(listing_id)
        return SellerListingResponse.model_validate(listing)

    async def archive(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListingResponse:
        listing = await self.listings.archive(account_id, listing_id)
        return SellerListingResponse.model_validate(listing)

    async def unarchive(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> SellerListingResponse:
        listing = await self.listings.unarchive(account_id, listing_id)
        return SellerListingResponse.model_validate(listing)

    async def delete_listing(
        self, account_id: uuid.UUID, listing_id: uuid.UUID
    ) -> None:
        await self.listings.delete(account_id, listing_id)

    # --- listing images ---------------------------------------------------

    async def list_images(self, listing_id: uuid.UUID) -> list[ListingImageResponse]:
        images = await self.images.list_by_listing(listing_id)
        return [await self._to_image_response(image) for image in images]

    async def upload_image(
        self,
        account_id: uuid.UUID,
        listing_id: uuid.UUID,
        *,
        file: UploadFile,
        is_primary: bool,
    ) -> ListingImageResponse:
        image = await self.images.upload(
            account_id, listing_id, file=file, is_primary=is_primary
        )
        return await self._to_image_response(image)

    async def delete_image(
        self, account_id: uuid.UUID, listing_id: uuid.UUID, image_id: uuid.UUID
    ) -> None:
        await self.images.delete(account_id, listing_id, image_id)

    async def _to_image_response(self, image: ListingImage) -> ListingImageResponse:
        url = await storage.get_public_url(
            image.cloudinary_public_id, resource_type=image.cloudinary_resource_type
        )
        return ListingImageResponse(
            id=image.id,
            listing_id=image.listing_id,
            url=url,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            created_at=image.created_at,
        )
