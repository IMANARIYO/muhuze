import uuid

from app.modules.catalog.repository import CatalogRepository
from app.modules.catalog.schemas import (
    CatalogImage,
    CatalogListingItem,
    CatalogOffer,
    CatalogProductDetail,
    CatalogProductRef,
    CatalogSellerRef,
    CatalogVariantAttribute,
    CatalogVariantDetail,
    CatalogVariantRef,
)
from app.modules.products.exceptions import ProductNotFoundError
from app.modules.products.models import (
    SellerListing,
    VariantAttributeValue,
)

_ACTIVE = "active"


class CatalogService:
    """Business+assembly rules for the buyer-facing catalog. This is
    read-only and public — no auth, intentional. Only ever returns
    `active` rows (product, variant, and listing must all be active) so a
    buyer never sees a draft/rejected/suspended offer."""

    def __init__(self, catalog: CatalogRepository) -> None:
        self.catalog = catalog

    async def search_active_listings(
        self,
        *,
        category_id: uuid.UUID | None,
        brand_id: uuid.UUID | None,
        search: str | None,
        sort: str | None,
    ) -> list[CatalogListingItem]:
        listings = await self.catalog.list_active_listings(
            category_id=category_id, brand_id=brand_id, search=search, sort=sort
        )
        return await self._assemble_listing_items(listings)

    async def get_product_detail(
        self, product_id: uuid.UUID
    ) -> CatalogProductDetail:
        product = await self.catalog.get_product_detail(product_id)
        if product is None:
            raise ProductNotFoundError()
        if product.status != _ACTIVE:
            raise ProductNotFoundError()

        images = await self.catalog.list_images_by_product([product.id])
        variant_rows = await self.catalog.list_active_variants_by_product(product.id)
        variant_ids = [v.id for v in variant_rows]
        variants_by_id = {v.id: v for v in variant_rows}

        values_by_variant = await self.catalog.list_attribute_values_for(variant_ids)
        attribute_ids = {
            v.attribute_id
            for values in values_by_variant.values()
            for v in values
        }
        attribute_names = await self.catalog.list_attributes_by_ids(list(attribute_ids))

        offers_by_variant = await self.catalog.list_active_listings_by_variants(
            variant_ids
        )
        offer_seller_ids = {
            listing.seller_id
            for offers in offers_by_variant.values()
            for listing in offers
        }
        sellers = await self.catalog.list_sellers_by_ids(list(offer_seller_ids))

        variants: list[CatalogVariantDetail] = []
        for variant_id in variant_ids:
            variant = variants_by_id[variant_id]
            attribute_values = self._variant_attributes(
                values_by_variant.get(variant_id, []), attribute_names
            )
            offers = [
                CatalogOffer(
                    listing_id=listing.id,
                    price=float(listing.price),
                    stock=listing.stock,
                    condition=listing.condition,
                    seller=CatalogSellerRef(
                        id=listing.seller_id,
                        business_name=sellers[listing.seller_id].business_name,
                    ),
                )
                for listing in offers_by_variant.get(variant_id, [])
            ]
            variants.append(
                CatalogVariantDetail(
                    id=variant.id,
                    sku_code=variant.sku_code,
                    attribute_values=attribute_values,
                    offers=offers,
                )
            )

        return CatalogProductDetail(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description,
            category_id=product.category_id,
            brand_id=product.brand_id,
            images=[
                await self._to_catalog_image(image) for image in images.get(product.id, [])
            ],
            variants=variants,
        )

    async def _assemble_listing_items(
        self, listings: list[SellerListing]
    ) -> list[CatalogListingItem]:
        if not listings:
            return []

        variant_ids = [l.variant_id for l in listings]
        seller_ids = [l.seller_id for l in listings]
        variants_by_id = await self.catalog.list_variants_by_ids(variant_ids)
        products_by_id = await self.catalog.list_products_by_ids(
            list({v.product_id for v in variants_by_id.values()})
        )
        sellers_by_id = await self.catalog.list_sellers_by_ids(seller_ids)
        values_by_variant = await self.catalog.list_attribute_values_for(variant_ids)
        attribute_ids = {
            v.attribute_id for values in values_by_variant.values() for v in values
        }
        attribute_names = await self.catalog.list_attributes_by_ids(list(attribute_ids))
        images_by_product = await self.catalog.list_images_by_product(
            list(products_by_id.keys())
        )

        items: list[CatalogListingItem] = []
        for listing in listings:
            variant = variants_by_id.get(listing.variant_id)
            if variant is None:
                continue
            product = products_by_id.get(variant.product_id)
            if product is None:
                continue
            seller = sellers_by_id.get(listing.seller_id)
            if seller is None:
                continue
            items.append(
                CatalogListingItem(
                    listing_id=listing.id,
                    price=float(listing.price),
                    stock=listing.stock,
                    condition=listing.condition,
                    product=CatalogProductRef(
                        id=product.id,
                        name=product.name,
                        slug=product.slug,
                        description=product.description,
                        category_id=product.category_id,
                    ),
                    variant=CatalogVariantRef(
                        id=variant.id,
                        sku_code=variant.sku_code,
                        attribute_values=self._variant_attributes(
                            values_by_variant.get(variant.id, []), attribute_names
                        ),
                    ),
                    seller=CatalogSellerRef(
                        id=listing.seller_id, business_name=seller.business_name
                    ),
                    images=[
                        await self._to_catalog_image(image)
                        for image in images_by_product.get(product.id, [])
                    ],
                )
            )
        return items

    def _variant_attributes(
        self,
        values: list[VariantAttributeValue],
        attribute_names: dict[uuid.UUID, str],
    ) -> list[CatalogVariantAttribute]:
        return [
            CatalogVariantAttribute(
                attribute_id=value.attribute_id,
                attribute_name=attribute_names.get(value.attribute_id, ""),
                value=value.value,
            )
            for value in values
        ]

    async def _to_catalog_image(self, image) -> CatalogImage:
        from app.core import storage

        url = await storage.get_public_url(
            image.cloudinary_public_id, resource_type=image.cloudinary_resource_type
        )
        return CatalogImage(
            id=image.id,
            url=url,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
        )
