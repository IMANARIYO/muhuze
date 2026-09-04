import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.orders.repository import OrderRepository
from app.modules.orders.fulfillment import create_seller_orders_for_order
from app.modules.payments.exceptions import (
    PaymentAlreadyProcessedError,
    PaymentNotFoundError,
)
from app.modules.payments.gateway import MomoGateway, get_momo_gateway
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.revenue.service import RevenueService


class PaymentService:
    """Lifecycle of a payment for an order, over mobile money (Airtel).

    v1 has no live PSP: `create` asks the (stub) Momo gateway for a payment
    request — the buyer's `momo_phone` is charged and the gateway returns a
    `request_reference` stored as `provider_ref`; the order stays `pending`.

    Money-in is confirmed in two steps because payment happens *outside* the
    app (the buyer sends MoMo to MUHUZE's number via USSD/app):
      * `report_paid`  — the buyer reports they sent it (`pending -> awaiting`);
        nothing is derived yet.
      * `confirm_paid` — MUHUZE admin verifies the money actually arrived
        (`awaiting -> paid`); THIS derives each seller's revenue AND opens
        each seller's fulfillment `seller_order` in the SAME DB transaction
        as the payment/order state change, so all money facts commit together
        or not at all.
    """

    def __init__(
        self,
        db: AsyncSession,
        gateway: MomoGateway | None = None,
    ) -> None:
        self.repo = PaymentRepository(db)
        self.orders = OrderRepository(db)
        self.revenue = RevenueService(db)
        self.db = db
        self.gateway = gateway or get_momo_gateway()

    async def create_payment(
        self,
        buyer_account_id: uuid.UUID,
        order_id: uuid.UUID,
        *,
        momo_phone: str | None = None,
        airtel_phone: str | None = None,
        method: str | None = None,
    ) -> Payment:
        order = await self._get_owned_order(buyer_account_id, order_id)
        existing = await self.repo.get_for_order(order.id)
        if existing is not None:
            if existing.status == PaymentStatus.PENDING:
                return existing
            raise PaymentAlreadyProcessedError()

        request_reference = self.gateway.request_payment(
            amount=float(order.total_amount),
            currency=order.currency,
            payer_phone=momo_phone,
            payee_phone=airtel_phone,
        )
        return await self.repo.create(
            order_id=order.id,
            amount=float(order.total_amount),
            currency=order.currency,
            method=method,
            momo_phone=momo_phone,
            airtel_phone=airtel_phone,
            provider_ref=request_reference,
        )

    async def report_paid(self, payment_id: uuid.UUID) -> Payment:
        """Buyer reports they sent the money outside the app.

        Moves the payment `pending -> awaiting`. Nothing is derived yet: the
        admin must *confirm* the money actually arrived for revenue and
        seller-orders to be created (see `confirm_paid`). Idempotent — a
        payment already `awaiting` (or beyond) is rejected by the caller."""
        payment = await self.repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.status != PaymentStatus.PENDING:
            raise PaymentAlreadyProcessedError()
        return await self.repo.mark_awaiting(payment)

    async def confirm_paid(
        self, payment_id: uuid.UUID
    ) -> tuple[Payment, int]:
        """MUHUZE admin confirms the money actually arrived.

        This is the moment the money really clears: it derives each seller's
        revenue (commission split at the seller's rate), opens each seller's
        fulfillment `seller_order` (so the seller sees the order in their
        dashboard), and flips the payment and order to `paid` — all in one
        DB transaction, or not at all. Idempotent: a payment already `paid`
        cannot be double-confirmed."""
        payment = await self.repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.status != PaymentStatus.AWAITING:
            raise PaymentAlreadyProcessedError()

        order = await self.orders.get_by_id(payment.order_id)
        if order is None:
            raise PaymentNotFoundError()

        lines = await self.revenue.record_for_paid_order(payment, order)
        await create_seller_orders_for_order(self.db, order)

        paid_at = datetime.now(UTC)
        await self.repo.mark_paid(payment, paid_at=paid_at)
        await self.orders.update(
            order,
            payment_status=OrderPaymentStatus.PAID,
            paid_at=paid_at,
        )
        return payment, len(lines)

    async def mark_failed(self, payment_id: uuid.UUID) -> Payment:
        payment = await self.repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.status != PaymentStatus.PENDING:
            raise PaymentAlreadyProcessedError()
        await self.repo.mark_failed(payment)
        order = await self.orders.get_by_id(payment.order_id)
        if order is not None:
            await self.orders.update(
                order, payment_status=OrderPaymentStatus.FAILED
            )
        return payment

    async def get_payment(self, payment_id: uuid.UUID) -> Payment:
        payment = await self.repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        return payment

    async def _get_owned_order(self, buyer_account_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        order = await self.orders.get_by_id(order_id)
        if order is None or order.buyer_account_id != buyer_account_id:
            raise PaymentNotFoundError()
        return order
