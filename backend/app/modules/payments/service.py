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
    `mark_paid` is the provider-callback/confirmation moment: it derives
    MUHUZE's revenue AND opens each seller's `seller_order` (fulfillment) in
    the SAME DB transaction as the payment/order state change, so all money
    facts commit together or not at all.
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
        momo_phone: str,
        airtel_phone: str,
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

    async def mark_paid(
        self, payment_id: uuid.UUID, provider_ref: str | None = None
    ) -> tuple[Payment, int]:
        payment = await self.repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.status != PaymentStatus.PENDING:
            raise PaymentAlreadyProcessedError()

        reference = provider_ref or payment.provider_ref or ""
        if not self.gateway.confirm_payment(reference):
            raise PaymentNotFoundError()

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
