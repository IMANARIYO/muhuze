import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import (
    Attribute,
    Brand,
    ListingImage,
    Product,
    ProductImage,
    ProductVariant,
    SellerListing,
    VariantAttributeValue,
)


class BrandRepository:
    """Data access for brands. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, brand_id: uuid.UUID) -> Brand | None:
        result = await self.db.execute(select(Brand).where(Brand.id == brand_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Brand | None:
        result = await self.db.execute(select(Brand).where(Brand.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def get_by_name(self, name: str) -> Brand | None:
        result = await self.db.execute(select(Brand).where(Brand.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Brand]:
        result = await self.db.execute(select(Brand).order_by(Brand.name))
        return list(result.scalars().all())

    async def create(self, *, name: str, slug: str, description: str | None) -> Brand:
        brand = Brand(name=name, slug=slug, description=description)
        self.db.add(brand)
        await self.db.flush()
        await self.db.refresh(brand)
        return brand

    async def update(
        self, brand: Brand, *, name: str, description: str | None, status: str
    ) -> Brand:
        brand.name = name
        brand.description = description
        brand.status = status
        await self.db.flush()
        await self.db.refresh(brand)
        return brand


class AttributeRepository:
    """Data access for attributes. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, attribute_id: uuid.UUID) -> Attribute | None:
        result = await self.db.execute(
            select(Attribute).where(Attribute.id == attribute_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Attribute | None:
        result = await self.db.execute(select(Attribute).where(Attribute.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def list_all(self) -> list[Attribute]:
        result = await self.db.execute(select(Attribute).order_by(Attribute.name))
        return list(result.scalars().all())

    async def create(
        self, *, name: str, slug: str, input_type: str, unit: str | None
    ) -> Attribute:
        attribute = Attribute(name=name, slug=slug, input_type=input_type, unit=unit)
        self.db.add(attribute)
        await self.db.flush()
        await self.db.refresh(attribute)
        return attribute

    async def update(
        self,
        attribute: Attribute,
        *,
        name: str,
        input_type: str,
        unit: str | None,
        status: str,
    ) -> Attribute:
        attribute.name = name
        attribute.input_type = input_type
        attribute.unit = unit
        attribute.status = status
        await self.db.flush()
        await self.db.refresh(attribute)
        return attribute


class ProductRepository:
    """Data access for products. No business rules here — status-transition
    guards live in ProductService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None

    async def list_all(
        self,
        *,
        category_id: uuid.UUID | None,
        brand_id: uuid.UUID | None,
        status: str | None,
        search: str | None = None,
    ) -> list[Product]:
        query = select(Product).order_by(Product.name)
        if category_id is not None:
            query = query.where(Product.category_id == category_id)
        if brand_id is not None:
            query = query.where(Product.brand_id == brand_id)
        if status is not None:
            query = query.where(Product.status == status)
        if search is not None:
            query = query.where(Product.name.ilike(f"%{search}%"))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_seller(self, seller_id: uuid.UUID) -> list[Product]:
        result = await self.db.execute(
            select(Product)
            .where(Product.created_by_seller_id == seller_id)
            .order_by(Product.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        category_id: uuid.UUID,
        brand_id: uuid.UUID | None,
        name: str,
        slug: str,
        description: str | None,
        created_by_seller_id: uuid.UUID | None = None,
    ) -> Product:
        product = Product(
            category_id=category_id,
            brand_id=brand_id,
            name=name,
            slug=slug,
            description=description,
            created_by_seller_id=created_by_seller_id,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update_details(
        self,
        product: Product,
        *,
        category_id: uuid.UUID,
        brand_id: uuid.UUID | None,
        name: str,
        description: str | None,
    ) -> Product:
        product.category_id = category_id
        product.brand_id = brand_id
        product.name = name
        product.description = description
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update_status(
        self, product: Product, *, status: str, rejection_reason: str | None = None
    ) -> Product:
        product.status = status
        product.rejection_reason = rejection_reason
        await self.db.flush()
        await self.db.refresh(product)
        return product


class ProductVariantRepository:
    """Data access for product variants. No `relationship()` declarations
    are used anywhere in this codebase (see categories/sellers) — attribute
    values are fetched with their own query via `list_attribute_values` /
    `list_attribute_values_for_variants`, not eager-loaded."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, variant_id: uuid.UUID) -> ProductVariant | None:
        result = await self.db.execute(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )
        return result.scalar_one_or_none()

    async def list_by_product(self, product_id: uuid.UUID) -> list[ProductVariant]:
        result = await self.db.execute(
            select(ProductVariant)
            .where(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.created_at)
        )
        return list(result.scalars().all())

    async def create(
        self, *, product_id: uuid.UUID, sku_code: str | None
    ) -> ProductVariant:
        variant = ProductVariant(product_id=product_id, sku_code=sku_code)
        self.db.add(variant)
        await self.db.flush()
        await self.db.refresh(variant)
        return variant

    async def update(
        self, variant: ProductVariant, *, sku_code: str | None, status: str
    ) -> ProductVariant:
        variant.sku_code = sku_code
        variant.status = status
        await self.db.flush()
        await self.db.refresh(variant)
        return variant

    async def list_attribute_values(
        self, variant_id: uuid.UUID
    ) -> list[VariantAttributeValue]:
        result = await self.db.execute(
            select(VariantAttributeValue).where(
                VariantAttributeValue.variant_id == variant_id
            )
        )
        return list(result.scalars().all())

    async def list_attribute_values_for_variants(
        self, variant_ids: list[uuid.UUID]
    ) -> list[VariantAttributeValue]:
        if not variant_ids:
            return []
        result = await self.db.execute(
            select(VariantAttributeValue).where(
                VariantAttributeValue.variant_id.in_(variant_ids)
            )
        )
        return list(result.scalars().all())

    async def add_attribute_value(
        self, *, variant_id: uuid.UUID, attribute_id: uuid.UUID, value: str
    ) -> None:
        self.db.add(
            VariantAttributeValue(
                variant_id=variant_id, attribute_id=attribute_id, value=value
            )
        )
        await self.db.flush()


class ProductImageRepository:
    """Data access for product images. No Cloudinary calls here — those
    live in ProductImageService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, image_id: uuid.UUID) -> ProductImage | None:
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        return result.scalar_one_or_none()

    async def list_by_product(self, product_id: uuid.UUID) -> list[ProductImage]:
        result = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order)
        )
        return list(result.scalars().all())

    async def list_by_products(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[ProductImage]]:
        if not product_ids:
            return {}
        result = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.product_id.in_(product_ids))
            .order_by(ProductImage.sort_order)
        )
        grouped: dict[uuid.UUID, list[ProductImage]] = {}
        for image in result.scalars().all():
            grouped.setdefault(image.product_id, []).append(image)
        return grouped

    async def create(
        self,
        *,
        product_id: uuid.UUID,
        cloudinary_public_id: str,
        cloudinary_resource_type: str,
        original_filename: str | None,
        mime_type: str,
        file_size: int,
        sort_order: int,
        is_primary: bool,
    ) -> ProductImage:
        image = ProductImage(
            product_id=product_id,
            cloudinary_public_id=cloudinary_public_id,
            cloudinary_resource_type=cloudinary_resource_type,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        self.db.add(image)
        await self.db.flush()
        await self.db.refresh(image)
        return image

    async def delete(self, image: ProductImage) -> None:
        await self.db.delete(image)
        await self.db.flush()


class SellerListingRepository:
    """Data access for seller listings. No business rules here —
    status-transition guards live in SellerListingService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, listing_id: uuid.UUID) -> SellerListing | None:
        result = await self.db.execute(
            select(SellerListing).where(SellerListing.id == listing_id)
        )
        return result.scalar_one_or_none()

    async def list_by_seller(
        self, seller_id: uuid.UUID, status: str | None
    ) -> list[SellerListing]:
        query = (
            select(SellerListing)
            .where(SellerListing.seller_id == seller_id)
            .order_by(SellerListing.created_at.desc())
        )
        if status is not None:
            query = query.where(SellerListing.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all(self, status: str | None) -> list[SellerListing]:
        query = select(SellerListing).order_by(SellerListing.created_at.desc())
        if status is not None:
            query = query.where(SellerListing.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        seller_id: uuid.UUID,
        variant_id: uuid.UUID,
        price: float,
        stock: int,
        seller_sku: str | None,
        condition: str,
    ) -> SellerListing:
        listing = SellerListing(
            seller_id=seller_id,
            variant_id=variant_id,
            price=price,
            stock=stock,
            seller_sku=seller_sku,
            condition=condition,
        )
        self.db.add(listing)
        await self.db.flush()
        await self.db.refresh(listing)
        return listing

    async def update_details(
        self,
        listing: SellerListing,
        *,
        price: float,
        stock: int,
        seller_sku: str | None,
        condition: str,
    ) -> SellerListing:
        listing.price = price
        listing.stock = stock
        listing.seller_sku = seller_sku
        listing.condition = condition
        await self.db.flush()
        await self.db.refresh(listing)
        return listing

    async def update_price(
        self, listing: SellerListing, *, price: float
    ) -> SellerListing:
        listing.price = price
        await self.db.flush()
        await self.db.refresh(listing)
        return listing

    async def update_stock(
        self, listing: SellerListing, *, stock: int
    ) -> SellerListing:
        listing.stock = stock
        await self.db.flush()
        await self.db.refresh(listing)
        return listing

    async def update_status(
        self,
        listing: SellerListing,
        *,
        status: str,
        rejection_reason: str | None = None,
    ) -> SellerListing:
        listing.status = status
        if rejection_reason is not None:
            listing.rejection_reason = rejection_reason
        await self.db.flush()
        await self.db.refresh(listing)
        return listing

    async def delete(self, listing: SellerListing) -> None:
        await self.db.delete(listing)
        await self.db.flush()


class ListingImageRepository:
    """Data access for listing images. No Cloudinary calls here — those
    live in ListingImageService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, image_id: uuid.UUID) -> ListingImage | None:
        result = await self.db.execute(
            select(ListingImage).where(ListingImage.id == image_id)
        )
        return result.scalar_one_or_none()

    async def list_by_listing(self, listing_id: uuid.UUID) -> list[ListingImage]:
        result = await self.db.execute(
            select(ListingImage)
            .where(ListingImage.listing_id == listing_id)
            .order_by(ListingImage.sort_order)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        listing_id: uuid.UUID,
        cloudinary_public_id: str,
        cloudinary_resource_type: str,
        original_filename: str | None,
        mime_type: str,
        file_size: int,
        sort_order: int,
        is_primary: bool,
    ) -> ListingImage:
        image = ListingImage(
            listing_id=listing_id,
            cloudinary_public_id=cloudinary_public_id,
            cloudinary_resource_type=cloudinary_resource_type,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        self.db.add(image)
        await self.db.flush()
        await self.db.refresh(image)
        return image

    async def delete(self, image: ListingImage) -> None:
        await self.db.delete(image)
        await self.db.flush()
