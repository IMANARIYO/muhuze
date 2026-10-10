import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_dependencies import get_current_account
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.payments.payment_dependencies import get_payment_service
from app.modules.payments.payment_permissions import PAYMENT_DESTINATION_MANAGE, PAYMENT_VERIFY
from app.modules.payments.payment_schema import (
    PaymentDestinationCreateRequest,
    PaymentDestinationResponse,
    PaymentDestinationUpdateRequest,
    PaymentInstructionsResponse,
    PaymentResponse,
    PaymentSubmitRequest,
    ReasonRequest,
    StaffPaymentFilters,
    StaffPaymentResponse,
)
from app.modules.payments.payment_service import PaymentService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

payment_router = APIRouter()

ServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
# Paying for your own order needs a login only.
BuyerDep = Annotated[Account, Depends(get_current_account)]
VerifierDep = Annotated[Account, Depends(require_permission(PAYMENT_VERIFY))]
DestinationManagerDep = Annotated[Account, Depends(require_permission(PAYMENT_DESTINATION_MANAGE))]

PAYMENTS = ["Payments"]
DESTINATIONS = ["Payment destinations"]


def _destination(destination) -> PaymentDestinationResponse:
    return PaymentDestinationResponse.model_validate(destination)


# ── The buyer ────────────────────────────────────────────────────────────


@payment_router.get(
    "/orders/mine/{order_id}/payment",
    response_model=APIResponse[PaymentInstructionsResponse],
    tags=PAYMENTS,
)
async def get_payment_instructions(
    buyer: BuyerDep, order_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """How to pay for one of your orders: the amount, MUHUZE's accounts, and
    the payments you have already submitted."""
    instructions = await service.get_instructions(buyer_account_id=buyer.id, order_id=order_id)
    return success_response(data=instructions, message="Payment instructions retrieved")


@payment_router.post(
    "/orders/mine/{order_id}/payment",
    response_model=APIResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
    tags=PAYMENTS,
)
async def submit_payment(
    buyer: BuyerDep, order_id: uuid.UUID, payload: PaymentSubmitRequest, service: ServiceDep
) -> JSONResponse:
    """Tell MUHUZE you have paid: which account, and the transaction
    reference. The order is released once the payment has been checked."""
    payment = await service.submit_payment(
        buyer_account_id=buyer.id, order_id=order_id, payload=payload
    )
    return success_response(
        data=payment,
        message="Payment submitted. We will confirm it shortly.",
        status_code=status.HTTP_201_CREATED,
    )


# ── Staff: verifying payments ────────────────────────────────────────────


@payment_router.get(
    "/payments", response_model=APIResponse[Page[StaffPaymentResponse]], tags=PAYMENTS
)
async def list_payments(
    _: VerifierDep,
    pagination: PaginationDep,
    filters: Annotated[StaffPaymentFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every payment, longest-waiting first. Use `status=awaiting_verification`
    for the ones to check."""
    page = await service.list_payments(pagination, filters)
    return success_response(data=page, message="Payments retrieved")


@payment_router.get(
    "/payments/{payment_id}", response_model=APIResponse[StaffPaymentResponse], tags=PAYMENTS
)
async def get_payment(_: VerifierDep, payment_id: uuid.UUID, service: ServiceDep) -> JSONResponse:
    return success_response(data=await service.get_payment(payment_id), message="Payment retrieved")


@payment_router.post(
    "/payments/{payment_id}/approve",
    response_model=APIResponse[StaffPaymentResponse],
    tags=PAYMENTS,
)
async def approve_payment(
    staff: VerifierDep, payment_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Confirm, after checking MUHUZE's statement, that the money arrived.
    The order is released to its sellers. Safe to repeat."""
    payment = await service.approve(payment_id=payment_id, approved_by=staff.id)
    return success_response(data=payment, message="Payment confirmed")


@payment_router.post(
    "/payments/{payment_id}/reject",
    response_model=APIResponse[StaffPaymentResponse],
    tags=PAYMENTS,
)
async def reject_payment(
    staff: VerifierDep, payment_id: uuid.UUID, payload: ReasonRequest, service: ServiceDep
) -> JSONResponse:
    """The payment could not be found on the statement. The buyer sees the
    reason and can submit again."""
    payment = await service.reject(
        payment_id=payment_id, reason=payload.reason, rejected_by=staff.id
    )
    return success_response(data=payment, message="Payment rejected")


# ── Staff: MUHUZE's receiving accounts ───────────────────────────────────


@payment_router.get(
    "/payment-destinations",
    response_model=APIResponse[Page[PaymentDestinationResponse]],
    tags=DESTINATIONS,
)
async def list_destinations(
    _: DestinationManagerDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Every account MUHUZE receives money on, active first."""
    return success_response(
        data=await service.list_destinations(pagination), message="Destinations retrieved"
    )


@payment_router.post(
    "/payment-destinations",
    response_model=APIResponse[PaymentDestinationResponse],
    status_code=status.HTTP_201_CREATED,
    tags=DESTINATIONS,
)
async def create_destination(
    staff: DestinationManagerDep, payload: PaymentDestinationCreateRequest, service: ServiceDep
) -> JSONResponse:
    """Add an account buyers can pay MUHUZE on."""
    destination = await service.create_destination(payload=payload, created_by=staff.id)
    return success_response(
        data=_destination(destination),
        message="Destination created",
        status_code=status.HTTP_201_CREATED,
    )


@payment_router.patch(
    "/payment-destinations/{destination_id}",
    response_model=APIResponse[PaymentDestinationResponse],
    tags=DESTINATIONS,
)
async def update_destination(
    staff: DestinationManagerDep,
    destination_id: uuid.UUID,
    payload: PaymentDestinationUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Change an account's details. Past payments keep what they were made to."""
    destination = await service.update_destination(
        destination_id, payload=payload, updated_by=staff.id
    )
    return success_response(data=_destination(destination), message="Destination updated")


@payment_router.post(
    "/payment-destinations/{destination_id}/activate",
    response_model=APIResponse[PaymentDestinationResponse],
    tags=DESTINATIONS,
)
async def activate_destination(
    staff: DestinationManagerDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    destination = await service.set_destination_active(
        destination_id, active=True, changed_by=staff.id
    )
    return success_response(data=_destination(destination), message="Destination activated")


@payment_router.post(
    "/payment-destinations/{destination_id}/deactivate",
    response_model=APIResponse[PaymentDestinationResponse],
    tags=DESTINATIONS,
)
async def deactivate_destination(
    staff: DestinationManagerDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Stop showing an account to buyers. It also stops being the default."""
    destination = await service.set_destination_active(
        destination_id, active=False, changed_by=staff.id
    )
    return success_response(data=_destination(destination), message="Destination deactivated")


@payment_router.post(
    "/payment-destinations/{destination_id}/set-default",
    response_model=APIResponse[PaymentDestinationResponse],
    tags=DESTINATIONS,
)
async def set_default_destination(
    staff: DestinationManagerDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Show this account first to buyers. Replaces the current default."""
    destination = await service.set_default_destination(destination_id, changed_by=staff.id)
    return success_response(data=_destination(destination), message="Default destination set")


@payment_router.delete(
    "/payment-destinations/{destination_id}", response_model=APIResponse[None], tags=DESTINATIONS
)
async def delete_destination(
    staff: DestinationManagerDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Delete an account no payment ever used. Deactivate any other."""
    await service.delete_destination(destination_id, deleted_by=staff.id)
    return success_response(message="Destination deleted")
