import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payments.models import Payment


class PaymentRepository:
    """Data access for payments. No business rules here — those live in
    PaymentService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_for_order(self, order_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        amount: float,
        currency: str,
        method: str | None,
        momo_phone: str | None,
        airtel_phone: str | None,
        provider_ref: str | None,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            amount=amount,
            currency=currency,
            method=method,
            momo_phone=momo_phone,
            airtel_phone=airtel_phone,
            provider_ref=provider_ref,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def mark_awaiting(self, payment: Payment) -> Payment:
        from app.modules.payments.models import PaymentStatus

        payment.status = PaymentStatus.AWAITING
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def mark_paid(
        self, payment: Payment, *, paid_at
    ) -> Payment:
        from app.modules.payments.models import PaymentStatus

        payment.status = PaymentStatus.PAID
        payment.paid_at = paid_at
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def mark_failed(self, payment: Payment) -> Payment:
        from app.modules.payments.models import PaymentStatus

        payment.status = PaymentStatus.FAILED
        await self.db.flush()
        await self.db.refresh(payment)
        return payment
