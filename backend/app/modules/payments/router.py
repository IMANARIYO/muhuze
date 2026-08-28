import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.modules.auth.dependencies import get_current_account
from app.modules.auth.models import Account
from app.modules.payments.controller import PaymentController
from app.modules.payments.dependencies import get_payment_controller
from app.modules.payments.schemas import (
    CreatePaymentRequest,
    PaidPaymentResponse,
    PaymentResponse,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


class MarkPaidRequest(BaseModel):
    provider_ref: str | None = Field(default=None, max_length=255, description="Reserved for future PSP")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: CreatePaymentRequest,
    account: Account = Depends(get_current_account),
    controller: PaymentController = Depends(get_payment_controller),
) -> APIResponse[PaymentResponse]:
    """Create a payment intent for the caller's order (amount = order total)."""
    payment = await controller.create_payment(account, payload)
    return success_response(data=payment, message="Payment created")


@router.post("/{payment_id}/paid")
async def mark_paid(
    payment_id: uuid.UUID,
    payload: MarkPaidRequest,
    account: Account = Depends(get_current_account),
    controller: PaymentController = Depends(get_payment_controller),
) -> APIResponse[PaidPaymentResponse]:
    """Confirm money-in. This is the exact moment the MUHUZE commission split
    (7% premium / 12% basic) is derived into revenue_transactions — idempotent
    per (order, seller), and the order flips to `paid` in the same commit."""
    payment = await controller.mark_paid(payment_id, provider_ref=payload.provider_ref)
    return success_response(data=payment, message="Payment marked as paid")


@router.post("/{payment_id}/failed")
async def mark_failed(
    payment_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: PaymentController = Depends(get_payment_controller),
) -> APIResponse[PaymentResponse]:
    """Mark the payment as failed — the order remains unpaid."""
    payment = await controller.mark_failed(payment_id)
    return success_response(data=payment, message="Payment marked as failed")


@router.get("/{payment_id}")
async def get_payment(
    payment_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: PaymentController = Depends(get_payment_controller),
) -> APIResponse[PaymentResponse]:
    """A single payment's current state."""
    payment = await controller.get_payment(payment_id)
    return success_response(data=payment, message="Payment retrieved")
