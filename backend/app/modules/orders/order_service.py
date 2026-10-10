"""Orders: one checkout, split into one part per shop.
Rules are documented in docs/features/010_orders.md and README §8, §9, §11.

    Order                       the buyer's whole purchase; what gets paid
      └── SellerOrder           one shop's part: own status, own money split
            └── OrderItem       a product and quantity, as it was when bought

The cart lives in the frontend. `place_order` receives only product ids and
quantities; it reads every price itself and records a snapshot of the
product and of the seller's commission terms. Nothing recorded here is ever
recalculated from current data.

Money follows three events, each told to the wallet ledger in the same
transaction: paid (the seller's share goes to pending), receipt confirmed
(pending becomes available), rejected after payment (the earning is reversed).

Every public method is one unit of work and commits it, except `mark_paid`,
which the payments feature calls inside its own transaction.
"""

import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.orders.order_constants import (
    FINAL_SELLER_ORDER_STATUSES,
    IMAGE_URL_MAX_LENGTH,
    ORDER_NUMBER_PREFIX,
    OrderStatus,
    SellerOrderStatus,
)
from app.modules.orders.order_exceptions import (
    MixedCurrencyOrderError,
    OrderNotFoundError,
    OrderStatusConflictError,
    OwnProductOrderError,
    ProductsUnavailableError,
)
from app.modules.orders.order_model import Order, OrderItem, SellerOrder, SellerOrderEvent
from app.modules.orders.order_repository import OrderRepository
from app.modules.orders.order_schema import (
    BuyerSellerOrderResponse,
    DeliveryResponse,
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
    OrderSummaryResponse,
    OwnOrderFilters,
    SellerOrderEventResponse,
    SellerOrderFilters,
    SellerOrderResponse,
    SellerOrderSummaryResponse,
    StaffOrderFilters,
    StaffOrderResponse,
    StaffSellerOrderResponse,
)
from app.modules.products.product_exceptions import ProductNotFoundError
from app.modules.products.product_schema import PublicProductResponse
from app.modules.products.product_service import ProductService
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_service import SellerService
from app.modules.wallets.wallet_service import WalletService
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

CENT = Decimal("0.01")
S = SellerOrderStatus


def derive_order_status(order: Order, seller_order_statuses: list[str]) -> OrderStatus:
    """The overall status of an order, worked out from payment and its parts.
    The ONLY place this is decided (README §9.3)."""
    if order.cancelled_at is not None:
        return OrderStatus.CANCELLED
    if order.paid_at is None:
        return OrderStatus.AWAITING_PAYMENT
    if all(status in FINAL_SELLER_ORDER_STATUSES for status in seller_order_statuses):
        # Every shop is done. If at least one delivered, the purchase
        # happened; if every shop rejected, nothing was bought.
        if any(status == S.COMPLETED for status in seller_order_statuses):
            return OrderStatus.COMPLETED
        return OrderStatus.CANCELLED
    return OrderStatus.IN_PROGRESS


def split_commission(subtotal: Decimal, rate: Decimal) -> tuple[Decimal, Decimal]:
    """(MUHUZE's commission, the seller's amount) for one seller order.

    The commission is rounded half up to the cent; the seller gets the rest,
    so the two always add up to the subtotal exactly (README §20 C13).
    """
    commission = (subtotal * rate / Decimal(100)).quantize(CENT, rounding=ROUND_HALF_UP)
    return commission, subtotal - commission


class OrderService:
    def __init__(
        self,
        session: AsyncSession,
        product_service: ProductService,
        seller_plan_service: SellerPlanService,
        seller_service: SellerService,
        wallet_service: WalletService,
    ) -> None:
        self._session = session
        self._products = product_service
        self._plans = seller_plan_service
        self._sellers = seller_service
        self._wallets = wallet_service
        self._repository = OrderRepository(session)

    # ── Used by the payments feature (no commit) ─────────────────────────

    async def mark_paid(self, order_id: uuid.UUID) -> Order:
        """Record that the order's payment is confirmed, and release each
        shop's part to its seller. Idempotent: a second call changes nothing.
        Not committed: the payment confirmation owns the transaction."""
        order = await self._locked(order_id)
        if order.paid_at is not None:
            return order
        if order.cancelled_at is not None:
            raise OrderStatusConflictError("A cancelled order cannot be paid")
        order.paid_at = utc_now()
        seller_orders = await self._repository.list_seller_orders_of([order.id])
        for seller_order in seller_orders:
            await self._move(seller_order, S.PENDING, actor_id=None)
            # The sale's revenue split and the seller's pending earning,
            # from the amounts frozen on the seller order (README §13.6).
            await self._wallets.record_earning(
                seller_order_id=seller_order.id,
                order_id=order.id,
                seller_id=seller_order.seller_id,
                gross_amount=seller_order.subtotal,
                commission_rate=seller_order.commission_rate,
                commission_amount=seller_order.commission_amount,
                seller_amount=seller_order.seller_amount,
                currency=order.currency,
            )
        self._refresh_status(order, seller_orders)
        await self._session.flush()
        logger.info("order paid", extra={"order_id": str(order.id)})
        return order

    async def get_order_of_buyer(
        self, *, buyer_account_id: uuid.UUID, order_id: uuid.UUID
    ) -> Order:
        """The buyer's own order, or "not found". For features (payments) that
        act on an order on the buyer's behalf."""
        return await self._own(buyer_account_id, order_id)

    # ── The buyer ────────────────────────────────────────────────────────

    async def place_order(
        self, *, buyer_account_id: uuid.UUID, payload: OrderCreateRequest
    ) -> OrderResponse:
        """Create the order, its part for each shop, and its items, in one
        transaction: either the whole order exists or none of it does."""
        quantities = {item.product_id: item.quantity for item in payload.items}
        products = await self._purchasable_products(list(quantities))

        own_seller_id = await self._sellers.find_seller_id(buyer_account_id)
        if any(product.seller_id == own_seller_id for product in products):
            raise OwnProductOrderError()
        currencies = {product.currency for product in products}
        if len(currencies) != 1:
            raise MixedCurrencyOrderError()

        by_seller: dict[uuid.UUID, list[PublicProductResponse]] = {}
        for product in products:
            by_seller.setdefault(product.seller_id, []).append(product)

        now = utc_now()
        delivery = payload.delivery
        order = Order(
            id=uuid.uuid4(),
            order_number=f"{ORDER_NUMBER_PREFIX}{await self._repository.next_order_number():06d}",
            buyer_account_id=buyer_account_id,
            status=OrderStatus.AWAITING_PAYMENT.value,
            currency=currencies.pop(),
            total_amount=Decimal(0),
            recipient_name=delivery.recipient_name,
            recipient_phone=delivery.recipient_phone,
            delivery_province=delivery.province,
            delivery_district=delivery.district,
            delivery_sector=delivery.sector,
            delivery_address=delivery.address or None,
            buyer_note=payload.note or None,
        )
        seller_orders, items, events = [], [], []
        for seller_id, seller_products in by_seller.items():
            # The commission terms in force right now, copied onto the order.
            terms = await self._plans.resolve_commercial_terms(seller_id, now)
            seller_order_id = uuid.uuid4()
            subtotal = Decimal(0)
            for product in seller_products:
                quantity = quantities[product.id]
                line_total = (product.price * quantity).quantize(CENT)
                subtotal += line_total
                items.append(
                    OrderItem(
                        seller_order_id=seller_order_id,
                        product_id=product.id,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=quantity,
                        line_total=line_total,
                        image_url=(product.main_image_url or "")[:IMAGE_URL_MAX_LENGTH] or None,
                        attributes=_attribute_snapshot(product),
                    )
                )
            commission, seller_amount = split_commission(subtotal, terms.commission_rate)
            seller_orders.append(
                SellerOrder(
                    id=seller_order_id,
                    order_id=order.id,
                    seller_id=seller_id,
                    seller_name=seller_products[0].shop.name,
                    status=S.AWAITING_PAYMENT.value,
                    subtotal=subtotal,
                    commission_rate=terms.commission_rate,
                    commission_amount=commission,
                    seller_amount=seller_amount,
                    terms_source=terms.source.value,
                    subscription_id=terms.subscription_id,
                    plan_name=terms.plan_name,
                    default_rate_id=terms.default_rate_id,
                )
            )
            events.append(
                SellerOrderEvent(
                    seller_order_id=seller_order_id,
                    from_status=None,
                    to_status=S.AWAITING_PAYMENT.value,
                    actor_account_id=buyer_account_id,
                )
            )
        # The total is computed from the parts, never the other way round.
        order.total_amount = sum((so.subtotal for so in seller_orders), Decimal(0))

        await self._repository.add_all([order])
        await self._repository.add_all(seller_orders)
        await self._repository.add_all([*items, *events])
        await self._session.commit()
        logger.info(
            "order placed",
            extra={
                "order_id": str(order.id),
                "order_number": order.order_number,
                "seller_orders": len(seller_orders),
            },
        )
        return await self._buyer_response(order)

    async def list_own_orders(
        self, *, buyer_account_id: uuid.UUID, pagination: PaginationParams, filters: OwnOrderFilters
    ) -> Page[OrderSummaryResponse]:
        orders, total = await self._repository.list_orders(
            pagination,
            buyer_account_id=buyer_account_id,
            status=filters.status.value if filters.status else None,
        )
        return _summary_page(orders, total, pagination)

    async def get_own_order(
        self, *, buyer_account_id: uuid.UUID, order_id: uuid.UUID
    ) -> OrderResponse:
        return await self._buyer_response(await self._own(buyer_account_id, order_id))

    async def cancel_own_order(
        self, *, buyer_account_id: uuid.UUID, order_id: uuid.UUID, reason: str | None
    ) -> OrderResponse:
        """The buyer cancels the whole order. Only while it is unpaid."""
        order = await self._own(buyer_account_id, order_id, for_update=True)
        if order.cancelled_at is not None:
            raise OrderStatusConflictError("This order is already cancelled")
        if order.paid_at is not None:
            raise OrderStatusConflictError("A paid order cannot be cancelled")
        order.cancelled_at = utc_now()
        order.cancel_reason = reason
        seller_orders = await self._repository.list_seller_orders_of([order.id])
        for seller_order in seller_orders:
            await self._move(seller_order, S.CANCELLED, actor_id=buyer_account_id, reason=reason)
        self._refresh_status(order, seller_orders)
        await self._session.commit()
        logger.info("order cancelled by buyer", extra={"order_id": str(order.id)})
        return await self._buyer_response(order)

    async def confirm_receipt(
        self, *, buyer_account_id: uuid.UUID, order_id: uuid.UUID, seller_order_id: uuid.UUID
    ) -> OrderResponse:
        """The buyer says one shop's part arrived, which completes it."""
        order = await self._own(buyer_account_id, order_id, for_update=True)
        seller_order = await self._repository.get_seller_order(seller_order_id)
        if seller_order is None or seller_order.order_id != order.id:
            raise OrderNotFoundError()
        # The buyer may have it in hand before the seller marks it delivered.
        self._require(
            seller_order,
            {S.SHIPPED, S.DELIVERED},
            "You can confirm receipt once the seller has shipped it",
        )
        await self._move(seller_order, S.COMPLETED, actor_id=buyer_account_id)
        # The buyer has it: the seller's earning becomes withdrawable.
        await self._wallets.settle(seller_order.id)
        await self._finish_change(order)
        return await self._buyer_response(order)

    # ── The seller ───────────────────────────────────────────────────────

    async def list_shop_orders(
        self, *, seller_id: uuid.UUID, pagination: PaginationParams, filters: SellerOrderFilters
    ) -> Page[SellerOrderSummaryResponse]:
        rows, total = await self._repository.list_shop_orders(
            pagination, seller_id=seller_id, status=filters.status.value if filters.status else None
        )
        items = [_seller_summary_fields(seller_order, order) for seller_order, order in rows]
        return Page[SellerOrderSummaryResponse].build(
            [SellerOrderSummaryResponse(**fields) for fields in items], total, pagination
        )

    async def get_shop_order(
        self, *, seller_id: uuid.UUID, seller_order_id: uuid.UUID
    ) -> SellerOrderResponse:
        seller_order, order = await self._shop_order(seller_id, seller_order_id)
        return await self._seller_response(seller_order, order)

    async def accept(
        self, *, seller_id: uuid.UUID, seller_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> SellerOrderResponse:
        return await self._seller_step(
            seller_id, seller_order_id, actor_id, S.ACCEPTED, {S.PENDING}, "accepted"
        )

    async def reject(
        self, *, seller_id: uuid.UUID, seller_order_id: uuid.UUID, actor_id: uuid.UUID, reason: str
    ) -> SellerOrderResponse:
        """The seller declines their part, for example because the product has
        run out (there is no stock tracking). It is already paid, so the buyer
        is owed a refund, which staff handle (README §20 R1)."""
        return await self._seller_step(
            seller_id, seller_order_id, actor_id, S.REJECTED, {S.PENDING}, "rejected", reason
        )

    async def ship(
        self, *, seller_id: uuid.UUID, seller_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> SellerOrderResponse:
        return await self._seller_step(
            seller_id, seller_order_id, actor_id, S.SHIPPED, {S.ACCEPTED}, "shipped"
        )

    async def deliver(
        self, *, seller_id: uuid.UUID, seller_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> SellerOrderResponse:
        return await self._seller_step(
            seller_id, seller_order_id, actor_id, S.DELIVERED, {S.SHIPPED}, "delivered"
        )

    # ── Staff ────────────────────────────────────────────────────────────

    async def list_all_orders(
        self, pagination: PaginationParams, filters: StaffOrderFilters
    ) -> Page[OrderSummaryResponse]:
        orders, total = await self._repository.list_orders(
            pagination,
            buyer_account_id=filters.buyer_account_id,
            status=filters.status.value if filters.status else None,
            search=filters.q.strip() or None if filters.q else None,
        )
        return _summary_page(orders, total, pagination)

    async def get_any_order(self, order_id: uuid.UUID) -> StaffOrderResponse:
        order = await self._repository.get_order(order_id)
        if order is None:
            raise OrderNotFoundError()
        seller_orders = await self._repository.list_seller_orders_of([order.id])
        items, events = await self._items_and_events(seller_orders)
        return StaffOrderResponse(
            **OrderSummaryResponse.model_validate(order).model_dump(),
            buyer_account_id=order.buyer_account_id,
            cancel_reason=order.cancel_reason,
            delivery=_delivery(order),
            seller_orders=[
                StaffSellerOrderResponse(
                    **_buyer_part(so, items.get(so.id, [])).model_dump(),
                    commission_rate=so.commission_rate,
                    commission_amount=so.commission_amount,
                    seller_amount=so.seller_amount,
                    terms_source=so.terms_source,
                    plan_name=so.plan_name,
                    events=events.get(so.id, []),
                )
                for so in seller_orders
            ],
        )

    # ── Loading and ownership ────────────────────────────────────────────

    async def _locked(self, order_id: uuid.UUID) -> Order:
        order = await self._repository.get_order(order_id, for_update=True)
        if order is None:
            raise OrderNotFoundError()
        return order

    async def _own(
        self, buyer_account_id: uuid.UUID, order_id: uuid.UUID, *, for_update: bool = False
    ) -> Order:
        """The ownership check: another buyer's order is "not found"."""
        order = await self._repository.get_order(order_id, for_update=for_update)
        if order is None or order.buyer_account_id != buyer_account_id:
            raise OrderNotFoundError()
        return order

    async def _shop_order(
        self, seller_id: uuid.UUID, seller_order_id: uuid.UUID, *, for_update: bool = False
    ) -> tuple[SellerOrder, Order]:
        """A seller reaches only their own shop's part, and only once the
        order is paid. Anything else is "not found"."""
        seller_order = await self._repository.get_seller_order(seller_order_id)
        if seller_order is None or seller_order.seller_id != seller_id:
            raise OrderNotFoundError()
        order = await self._repository.get_order(seller_order.order_id, for_update=for_update)
        if order is None or order.paid_at is None:
            raise OrderNotFoundError()
        if for_update:
            # Re-read under the order lock, so the status checked is current.
            await self._session.refresh(seller_order)
        return seller_order, order

    async def _purchasable_products(
        self, product_ids: list[uuid.UUID]
    ) -> list[PublicProductResponse]:
        """Each product as a buyer can see it right now. One that isn't on
        sale, for whatever reason, makes the whole order fail, naming them."""
        products, unavailable = [], []
        for product_id in product_ids:
            try:
                products.append(await self._products.get_public_product(product_id))
            except ProductNotFoundError:
                unavailable.append(str(product_id))
        if unavailable:
            raise ProductsUnavailableError(
                f"These products are no longer available: {', '.join(unavailable)}"
            )
        return products

    # ── Status changes ───────────────────────────────────────────────────

    @staticmethod
    def _require(seller_order: SellerOrder, allowed: set[SellerOrderStatus], message: str) -> None:
        if seller_order.status not in allowed:
            raise OrderStatusConflictError(message)

    async def _move(
        self,
        seller_order: SellerOrder,
        to_status: SellerOrderStatus,
        *,
        actor_id: uuid.UUID | None,
        reason: str | None = None,
    ) -> None:
        """Change a seller order's status and record who did it and why."""
        from_status = seller_order.status
        seller_order.status = to_status.value
        seller_order.status_reason = reason
        await self._repository.add_all(
            [
                SellerOrderEvent(
                    seller_order_id=seller_order.id,
                    from_status=from_status,
                    to_status=to_status.value,
                    reason=reason,
                    actor_account_id=actor_id,
                )
            ]
        )

    @staticmethod
    def _refresh_status(order: Order, seller_orders: list[SellerOrder]) -> None:
        order.status = derive_order_status(order, [so.status for so in seller_orders]).value

    async def _finish_change(self, order: Order) -> None:
        """Re-derive the order's status from all its parts and commit, in the
        same transaction as the change that caused it."""
        self._refresh_status(order, await self._repository.list_seller_orders_of([order.id]))
        await self._session.commit()

    async def _seller_step(
        self,
        seller_id: uuid.UUID,
        seller_order_id: uuid.UUID,
        actor_id: uuid.UUID,
        to_status: SellerOrderStatus,
        allowed_from: set[SellerOrderStatus],
        verb: str,
        reason: str | None = None,
    ) -> SellerOrderResponse:
        seller_order, order = await self._shop_order(seller_id, seller_order_id, for_update=True)
        allowed = " or ".join(sorted(status.value for status in allowed_from))
        self._require(seller_order, allowed_from, f"Only an order that is {allowed} can be {verb}")
        await self._move(seller_order, to_status, actor_id=actor_id, reason=reason)
        if to_status == S.REJECTED:
            # A paid sale is undone: the seller's pending earning is taken back.
            await self._wallets.reverse(seller_order.id)
        await self._finish_change(order)
        logger.info(
            "seller order status changed",
            extra={
                "seller_order_id": str(seller_order.id),
                "order_id": str(order.id),
                "to_status": to_status.value,
            },
        )
        return await self._seller_response(seller_order, order)

    # ── Responses ────────────────────────────────────────────────────────

    async def _items_and_events(
        self, seller_orders: list[SellerOrder]
    ) -> tuple[
        dict[uuid.UUID, list[OrderItemResponse]], dict[uuid.UUID, list[SellerOrderEventResponse]]
    ]:
        ids = [seller_order.id for seller_order in seller_orders]
        items: dict[uuid.UUID, list[OrderItemResponse]] = {}
        for item in await self._repository.list_items(ids):
            items.setdefault(item.seller_order_id, []).append(
                OrderItemResponse.model_validate(item)
            )
        events: dict[uuid.UUID, list[SellerOrderEventResponse]] = {}
        for event in await self._repository.list_events(ids):
            events.setdefault(event.seller_order_id, []).append(
                SellerOrderEventResponse.model_validate(event)
            )
        return items, events

    async def _buyer_response(self, order: Order) -> OrderResponse:
        seller_orders = await self._repository.list_seller_orders_of([order.id])
        items, _ = await self._items_and_events(seller_orders)
        return OrderResponse(
            **OrderSummaryResponse.model_validate(order).model_dump(),
            cancel_reason=order.cancel_reason,
            delivery=_delivery(order),
            seller_orders=[_buyer_part(so, items.get(so.id, [])) for so in seller_orders],
        )

    async def _seller_response(
        self, seller_order: SellerOrder, order: Order
    ) -> SellerOrderResponse:
        items, events = await self._items_and_events([seller_order])
        return SellerOrderResponse(
            **_seller_summary_fields(seller_order, order),
            seller_id=seller_order.seller_id,
            order_id=order.id,
            status_reason=seller_order.status_reason,
            commission_rate=seller_order.commission_rate,
            commission_amount=seller_order.commission_amount,
            plan_name=seller_order.plan_name,
            delivery=_delivery(order),
            items=items.get(seller_order.id, []),
            events=events.get(seller_order.id, []),
        )


def _attribute_snapshot(product: PublicProductResponse) -> list[dict]:
    """The product's details as plain display values, frozen onto the order."""
    snapshot = []
    for attribute in product.attributes:
        value = attribute.value
        if isinstance(value, list):
            value = [option.value for option in value]
        elif not isinstance(value, bool | int | float | str):
            value = value.value  # a single chosen option
        snapshot.append({"name": attribute.name, "value": value, "unit": attribute.unit})
    return snapshot


def _delivery(order: Order) -> DeliveryResponse:
    return DeliveryResponse(
        recipient_name=order.recipient_name,
        recipient_phone=order.recipient_phone,
        province=order.delivery_province,
        district=order.delivery_district,
        sector=order.delivery_sector,
        address=order.delivery_address,
        note=order.buyer_note,
    )


def _buyer_part(
    seller_order: SellerOrder, items: list[OrderItemResponse]
) -> BuyerSellerOrderResponse:
    return BuyerSellerOrderResponse(
        id=seller_order.id,
        seller_id=seller_order.seller_id,
        seller_name=seller_order.seller_name,
        status=seller_order.status,
        status_reason=seller_order.status_reason,
        subtotal=seller_order.subtotal,
        items=items,
    )


def _seller_summary_fields(seller_order: SellerOrder, order: Order) -> dict:
    return {
        "id": seller_order.id,
        "order_number": order.order_number,
        "status": seller_order.status,
        "currency": order.currency,
        "subtotal": seller_order.subtotal,
        "seller_amount": seller_order.seller_amount,
        "recipient_name": order.recipient_name,
        "paid_at": order.paid_at,
        "created_at": seller_order.created_at,
    }


def _summary_page(
    orders: list[Order], total: int, pagination: PaginationParams
) -> Page[OrderSummaryResponse]:
    items = [OrderSummaryResponse.model_validate(order) for order in orders]
    return Page[OrderSummaryResponse].build(items, total, pagination)
