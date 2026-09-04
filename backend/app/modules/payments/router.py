import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import get_current_account, require_role
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
async def report_paid(
    payment_id: uuid.UUID,
    account: Account = Depends(get_current_account),
    controller: PaymentController = Depends(get_payment_controller),
) -> APIResponse[PaymentResponse]:
    """Buyer reports they sent the money outside the app (pending -> awaiting).

    This does NOT yet derive revenue or open seller orders — it only flags the
    payment for MUHUZE admin to verify. The sellers only see the order and
    their money once an admin confirms actual receipt (POST .../confirm)."""
    payment = await controller.report_paid(payment_id)
    return success_response(data=payment, message="Payment reported — awaiting admin confirmation")


@router.post("/{payment_id}/confirm")
async def confirm_paid(
    payment_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: PaymentController = Depends(get_payment_controller),
) -> APIResponse[PaidPaymentResponse]:
    """MUHUZE admin confirms the money actually arrived (awaiting -> paid).

    This is the exact moment the MUHUZE commission split (7% premium / 12%
    basic) is derived into revenue_transactions and each seller's order is
    opened, so the sellers see the order and their earnings. Idempotent per
    (order, seller); the order flips to `paid` in the same commit."""
    payment = await controller.confirm_paid(payment_id)
    return success_response(data=payment, message="Money received — payment confirmed")


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
