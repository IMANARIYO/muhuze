import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.carts.exceptions import CartItemNotFoundError
from app.modules.carts.models import CartItem
from app.modules.carts.repository import CartItemRepository
from app.modules.carts.schemas import AddCartItemRequest, UpdateCartItemRequest
from app.modules.products.models import (
    Product,
    ProductImage,
    SellerListing,
    VariantAttributeValue,
)
from app.modules.products.repository import (
    ProductImageRepository,
    ProductRepository,
    ProductVariantRepository,
    SellerListingRepository,
)
from app.modules.sellers.repository import SellerRepository


class CartService:
    """Business rules for the cart. The cart is a *customer interaction
    mechanism* — temporary and editable — as opposed to the `Order`, which is
    the permanent financial record (see orders module)."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = CartItemRepository(db)
        self.listings = SellerListingRepository(db)
        self.variants = ProductVariantRepository(db)
        self.products = ProductRepository(db)
        self.sellers = SellerRepository(db)
        self.images = ProductImageRepository(db)

    async def add_item(
        self, account_id: uuid.UUID, payload: AddCartItemRequest
    ) -> CartItem:
        """Add a listing to the cart, or bump the quantity if it's already
        there (unique per account+listing). The listing must exist and be
        purchasable."""
        listing = await self.listings.get_by_id(payload.listing_id)
        if listing is None or listing.status != "active":
            raise CartItemNotFoundError(message="This listing is not available")

        existing = await self.repo.get_for_account_and_listing(
            account_id, payload.listing_id
        )
        if existing is not None:
            return await self.repo.update_quantity(
                existing, quantity=existing.quantity + payload.quantity
            )
        return await self.repo.create(
            account_id=account_id,
            listing_id=payload.listing_id,
            quantity=payload.quantity,
        )

    async def update_quantity(
        self, account_id: uuid.UUID, item_id: uuid.UUID, payload: UpdateCartItemRequest
    ) -> CartItem:
        item = await self._get_owned_item(account_id, item_id)
        return await self.repo.update_quantity(item, quantity=payload.quantity)

    async def remove_item(self, account_id: uuid.UUID, item_id: uuid.UUID) -> None:
        item = await self._get_owned_item(account_id, item_id)
        await self.repo.delete(item)

    async def clear(self, account_id: uuid.UUID) -> None:
        await self.repo.clear_for_account(account_id)

    async def get_cart(self, account_id: uuid.UUID) -> dict:
        """The buyer's cart with display info (product name, variant label,
        price, line subtotals) plus the gross total. Prices are read from the
        *current* listings at read time — the frozen prices are the order's
        job, not the cart's."""
        items = await self.repo.list_for_account(account_id)
        if not items:
            return {"items": [], "item_count": 0, "total": 0.0}

        listing_ids = [item.listing_id for item in items]
        listings = await self._listings_by_ids(listing_ids)
        variant_ids = [l.variant_id for l in listings if l is not None]
        products_by_variant = await self._products_by_variant_ids(variant_ids)
        product_ids = [
            p.id for p in products_by_variant.values() if p is not None
        ]
        images_by_product = await self._primary_images_by_product(product_ids)
        sellers_by_id = await self._sellers_by_ids(
            list({l.seller_id for l in listings if l is not None})
        )
        variant_labels = (
            await self.variants.list_attribute_values_for_variants(variant_ids)
            if variant_ids
            else []
        )
        labels_by_variant: dict[uuid.UUID, str] = _group_variant_labels(
            variant_labels
        )

        lines = []
        total = 0.0
        item_count = 0
        for item in items:
            listing = next((l for l in listings if l and l.id == item.listing_id), None)
            if listing is None:
                continue
            product = products_by_variant.get(listing.variant_id)
            image = next(
                iter(images_by_product.get(product.id, [])) if product else None
            )
            seller = sellers_by_id.get(listing.seller_id)
            unit_price = float(listing.price)
            subtotal = round(unit_price * item.quantity, 2)
            total = round(total + subtotal, 2)
            item_count += 1
            lines.append(
                {
                    "id": item.id,
                    "listing_id": item.listing_id,
                    "seller_id": listing.seller_id,
                    "seller_name": seller.business_name if seller else listing_id_short(listing.id),
                    "product_id": product.id if product else listing.variant_id,
                    "product_name": product.name if product else listing_id_short(listing.id),
                    "product_image": await _image_url(image),
                    "variant_name": labels_by_variant.get(listing.variant_id),
                    "unit_price": unit_price,
                    "condition": listing.condition,
                    "stock": listing.stock,
                    "quantity": item.quantity,
                    "subtotal": subtotal,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
            )
        return {"items": lines, "item_count": item_count, "total": total}

    async def _get_owned_item(
        self, account_id: uuid.UUID, item_id: uuid.UUID
    ) -> CartItem:
        item = await self.repo.get_by_id(item_id)
        if item is None or item.account_id != account_id:
            raise CartItemNotFoundError()
        return item

    async def _listings_by_ids(
        self, listing_ids: list[uuid.UUID]
    ) -> list[SellerListing | None]:
        result = []
        for listing_id in listing_ids:
            result.append(await self.listings.get_by_id(listing_id))
        return result

    async def _products_by_variant_ids(
        self, variant_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Product | None]:
        out: dict[uuid.UUID, Product | None] = {}
        for variant_id in variant_ids:
            variant = await self.variants.get_by_id(variant_id)
            if variant is None:
                out[variant_id] = None
                continue
            product = await self.products.get_by_id(variant.product_id)
            out[variant_id] = product
        return out

    async def _sellers_by_ids(
        self, seller_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, object]:
        return await self.sellers.list_by_ids(seller_ids)

    async def _primary_images_by_product(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, ProductImage | None]:
        images_by_product = await self.images.list_by_products(product_ids)
        out: dict[uuid.UUID, ProductImage | None] = {}
        for product_id, images in images_by_product.items():
            out[product_id] = next(
                (i for i in images if i.is_primary), images[0] if images else None
            )
        return out


def _group_variant_labels(
    values: list[VariantAttributeValue],
) -> dict[uuid.UUID, str]:
    grouped: dict[uuid.UUID, list[str]] = {}
    for value in values:
        grouped.setdefault(value.variant_id, []).append(value.value)
    return {
        variant_id: " / ".join(parts)
        for variant_id, parts in grouped.items()
        if parts
    }


def listing_id_short(listing_id: uuid.UUID) -> str:
    return str(listing_id)[:8]


async def _image_url(image: ProductImage | None) -> str | None:
    if image is None:
        return None
    from app.core import storage

    if storage.is_configured():
        return await storage.get_public_url(
            image.cloudinary_public_id,
            resource_type=image.cloudinary_resource_type,
        )
    return f"https://placehold.co/600x400?text={image.cloudinary_public_id[:8]}"
