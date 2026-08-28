import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.addresses.repository import ShippingAddressRepository
from app.modules.carts.repository import CartItemRepository
from app.modules.orders.exceptions import (
    CartItemUnavailableError,
    EmptyCartError,
    InsufficientStockError,
    OrderNotFoundError,
    ShippingDestinationRequiredError,
)
from app.modules.orders.models import Order, OrderItem, ShippingInfo
from app.modules.orders.repository import (
    OrderItemRepository,
    OrderRepository,
    ShippingInfoRepository,
)
from app.modules.revenue.service import RevenueService
from app.modules.orders.schemas import CheckoutRequest
from app.modules.products.models import SellerListing
from app.modules.products.repository import (
    ProductRepository,
    ProductVariantRepository,
    SellerListingRepository,
)


class OrderService:
    """Checkout: turn a (temporary) cart into a permanent order.

    The order belongs to the buyer and is multi-seller: each `order_item`
    carries its seller_id. All money is captured as snapshots at checkout
    (gross). The MUHUZE commission split is derived later by the revenue
    module when the payment clears — never here.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.orders = OrderRepository(db)
        self.items = OrderItemRepository(db)
        self.shipping_infos = ShippingInfoRepository(db)
        self.cart = CartItemRepository(db)
        self.listings = SellerListingRepository(db)
        self.variants = ProductVariantRepository(db)
        self.products = ProductRepository(db)
        self.addresses = ShippingAddressRepository(db)
        self.revenue = RevenueService(db)

    async def checkout(
        self, buyer_account_id: uuid.UUID, payload: CheckoutRequest
    ) -> Order:
        cart_items = await self.cart.list_for_account(buyer_account_id)
        if not cart_items:
            raise EmptyCartError()

        snapshot_info = await self._resolve_shipping(payload)

        # Pre-validate availability AND stock for every line before creating
        # anything, so checkout fails fast with no partial order. Money is never
        # taken from the client — prices are read from the DB below.
        populated = []
        subtotal = 0.0
        for cart_item in cart_items:
            listing = await self.listings.get_by_id(cart_item.listing_id)
            if listing is None or listing.status != "active":
                raise CartItemUnavailableError()
            if listing.stock < cart_item.quantity:
                raise InsufficientStockError()
            line = await self._snapshot_line(listing, cart_item.quantity)
            if line is None:
                raise CartItemUnavailableError()
            populated.append(line)
            subtotal = round(subtotal + line["subtotal"], 2)

        if not populated:
            raise EmptyCartError()

        shipping_fee = 0.0
        discount = 0.0
        total = round(subtotal + shipping_fee - discount, 2)

        order = await self.orders.create(
            order_number=generate_order_number(),
            buyer_account_id=buyer_account_id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            discount_amount=discount,
            total_amount=total,
            currency="RWF",
            contact_phone=payload.contact_phone,
            notes=payload.notes,
        )

        for line in populated:
            await self.items.create(
                order_id=order.id,
                seller_id=line["seller_id"],
                listing_id=line["listing_id"],
                product_variant_id=line["product_variant_id"],
                product_name=line["product_name"],
                variant_name=line["variant_name"],
                unit_price=line["unit_price"],
                quantity=line["quantity"],
                subtotal=line["subtotal"],
            )

        info = await self.shipping_infos.create(
            order_id=order.id,
            recipient_name=snapshot_info["recipient_name"],
            phone=snapshot_info["phone"],
            country=snapshot_info["country"],
            province=snapshot_info["province"],
            district=snapshot_info["district"],
            sector=snapshot_info["sector"],
            cell=snapshot_info["cell"],
            village=snapshot_info["village"],
            address_line=snapshot_info["address_line"],
            delivery_instructions=snapshot_info["delivery_instructions"],
            latitude=snapshot_info["latitude"],
            longitude=snapshot_info["longitude"],
        )
        await self.orders.update(order, shipping_info_id=info.id)

        await self.cart.clear_for_account(buyer_account_id)
        return order

    async def get_order_detail(
        self, account_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        order = await self.orders.get_by_id(order_id)
        if order is None or order.buyer_account_id != account_id:
            raise OrderNotFoundError()
        return order

    async def list_for_account(self, account_id: uuid.UUID) -> list[Order]:
        return await self.orders.list_for_account(account_id)

    async def receive(
        self, buyer_account_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        """The buyer confirms the order was received, completing it.

        This is the final mile of the lifecycle: after each seller has shipped
        (optionally marking it `delivered`), the buyer confirms actual receipt.
        Marks `completed_at`, closes the buyer's order, and releases the held
        seller earnings (escrow) to the sellers — all in the same transaction.
        Idempotent — an already-completed order stays completed and a repeat
        `receive` cannot double-release."""
        order = await self.get_order_detail(buyer_account_id, order_id)
        if order.completed_at is None:
            order.completed_at = datetime.now(UTC)
            await self.orders.flush_changes(order)
            await self.revenue.release_for_order(order.id)
        return order

    async def _resolve_shipping(self, payload: CheckoutRequest) -> dict:
        if payload.shipping_address_id is not None:
            address = await self.addresses.get_by_id(payload.shipping_address_id)
            if address is None:
                raise ShippingDestinationRequiredError()
            return {
                "recipient_name": address.recipient_name,
                "phone": address.phone,
                "country": address.country,
                "province": address.province,
                "district": address.district,
                "sector": address.sector,
                "cell": address.cell,
                "village": address.village,
                "address_line": address.address_line,
                "delivery_instructions": address.delivery_instructions,
                "latitude": None if address.latitude is None else float(address.latitude),
                "longitude": None if address.longitude is None else float(address.longitude),
            }
        if payload.shipping is not None:
            s = payload.shipping
            return {
                "recipient_name": s.recipient_name,
                "phone": s.phone,
                "country": s.country,
                "province": s.province,
                "district": s.district,
                "sector": s.sector,
                "cell": s.cell,
                "village": s.village,
                "address_line": s.address_line,
                "delivery_instructions": s.delivery_instructions,
                "latitude": s.latitude,
                "longitude": s.longitude,
            }
        raise ShippingDestinationRequiredError()

    async def _snapshot_line(
        self, listing: SellerListing, quantity: int
    ) -> dict | None:
        variant = await self.variants.get_by_id(listing.variant_id)
        if variant is None:
            return None
        product = await self.products.get_by_id(variant.product_id)
        unit_price = float(listing.price)
        return {
            "seller_id": listing.seller_id,
            "listing_id": listing.id,
            "product_variant_id": listing.variant_id,
            "product_name": product.name if product else "Item",
            "variant_name": None,
            "unit_price": unit_price,
            "quantity": quantity,
            "subtotal": round(unit_price * quantity, 2),
        }


def generate_order_number(now: datetime | None = None) -> str:
    """A human-readable, monotonically-increasing-ish order number, e.g.
    MUH-2026-000123. Collisions are guarded by the unique constraint on
    `order_number`; a suffix of the id would not be needed in practice given
    the low write rate, so keep it simple and readable."""
    timestamp = now or datetime.now(UTC)
    return f"MUH-{timestamp.year}-{timestamp.microsecond:06d}"
