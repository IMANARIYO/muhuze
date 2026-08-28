import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Account
from app.modules.payments.schemas import (
    CreatePaymentRequest,
    PaidPaymentResponse,
    PaymentResponse,
)
from app.modules.payments.service import PaymentService


class PaymentController:
    """Translates HTTP requests/responses to and from the payment service."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = PaymentService(db)

    async def create_payment(
        self, account: Account, payload: CreatePaymentRequest
    ) -> PaymentResponse:
        payment = await self.service.create_payment(
            account.id,
            payload.order_id,
            momo_phone=payload.momo_phone,
            airtel_phone=payload.airtel_phone,
            method=payload.method,
        )
        return PaymentResponse.model_validate(payment)

    async def mark_paid(
        self, payment_id: uuid.UUID, provider_ref: str | None = None
    ) -> PaidPaymentResponse:
        payment, revenue_count = await self.service.mark_paid(
            payment_id, provider_ref=provider_ref
        )
        response = PaymentResponse.model_validate(payment)
        return PaidPaymentResponse(
            **response.model_dump(), revenue=revenue_count
        )

    async def mark_failed(self, payment_id: uuid.UUID) -> PaymentResponse:
        payment = await self.service.mark_failed(payment_id)
        return PaymentResponse.model_validate(payment)

    async def get_payment(self, payment_id: uuid.UUID) -> PaymentResponse:
        payment = await self.service.get_payment(payment_id)
        return PaymentResponse.model_validate(payment)
