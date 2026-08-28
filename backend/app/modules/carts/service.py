import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.carts.exceptions import CartItemNotFoundError
from app.modules.carts.models import CartItem
from app.modules.carts.repository import CartItemRepository
from app.modules.carts.schemas import AddCartItemRequest, UpdateCartItemRequest
from app.modules.products.models import Product, SellerListing, VariantAttributeValue
from app.modules.products.repository import (
    ProductRepository,
    ProductVariantRepository,
    SellerListingRepository,
)


class CartService:
    """Business rules for the cart. The cart is a *customer interaction
    mechanism* — temporary and editable — as opposed to the `Order`, which is
    the permanent financial record (see orders module)."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = CartItemRepository(db)
        self.listings = SellerListingRepository(db)
        self.variants = ProductVariantRepository(db)
        self.products = ProductRepository(db)

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
        products = await self._products_by_variant_ids(variant_ids)
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
            product = products.get(listing.variant_id)
            unit_price = float(listing.price)
            subtotal = round(unit_price * item.quantity, 2)
            total = round(total + subtotal, 2)
            item_count += 1
            lines.append(
                {
                    "id": item.id,
                    "listing_id": item.listing_id,
                    "seller_id": listing.seller_id,
                    "product_name": product.name if product else listing_id_short(listing.id),
                    "variant_name": labels_by_variant.get(listing.variant_id),
                    "unit_price": unit_price,
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
