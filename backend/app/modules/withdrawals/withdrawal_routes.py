import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.sellers.seller_dependencies import get_current_active_seller
from app.modules.sellers.seller_model import Seller
from app.modules.withdrawals.withdrawal_dependencies import (
    get_destination_seller_id,
    get_own_seller_id,
    get_withdrawal_service,
)
from app.modules.withdrawals.withdrawal_permissions import (
    WITHDRAWAL_REQUEST,
    WITHDRAWAL_REVIEW,
)
from app.modules.withdrawals.withdrawal_schema import (
    CompleteRequest,
    PayoutDestinationCreateRequest,
    PayoutDestinationResponse,
    PayoutDestinationUpdateRequest,
    ReasonRequest,
    StaffWithdrawalFilters,
    StaffWithdrawalResponse,
    WithdrawalRequest,
    WithdrawalResponse,
)
from app.modules.withdrawals.withdrawal_service import WithdrawalService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

withdrawal_router = APIRouter()

ServiceDep = Annotated[WithdrawalService, Depends(get_withdrawal_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
OwnSellerIdDep = Annotated[uuid.UUID, Depends(get_own_seller_id)]
DestinationSellerIdDep = Annotated[uuid.UUID, Depends(get_destination_seller_id)]
ActiveSellerDep = Annotated[Seller, Depends(get_current_active_seller)]
RequesterDep = Annotated[Account, Depends(require_permission(WITHDRAWAL_REQUEST))]
ReviewerDep = Annotated[Account, Depends(require_permission(WITHDRAWAL_REVIEW))]

WITHDRAWALS = ["Withdrawals"]
DESTINATIONS = ["Payout destinations"]

# NOTE on ordering: /withdrawals/mine is declared before /withdrawals/{id}, so
# "mine" is never mistaken for a withdrawal id.


# ── The seller: payout destinations ──────────────────────────────────────


@withdrawal_router.get(
    "/withdrawal/destinations/mine",
    response_model=APIResponse[Page[PayoutDestinationResponse]],
    tags=DESTINATIONS,
)
async def list_my_destinations(
    seller_id: DestinationSellerIdDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Where you receive withdrawals, active first."""
    return success_response(
        data=await service.list_destinations(seller_id, pagination),
        message="Payout destinations retrieved",
    )


@withdrawal_router.post(
    "/withdrawal/destinations",
    response_model=APIResponse[PayoutDestinationResponse],
    status_code=status.HTTP_201_CREATED,
    tags=DESTINATIONS,
)
async def create_destination(
    seller_id: DestinationSellerIdDep,
    payload: PayoutDestinationCreateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Register an account where MUHUZE can pay you."""
    destination = await service.create_destination(seller_id, payload)
    return success_response(
        data=destination, message="Payout destination created", status_code=status.HTTP_201_CREATED
    )


@withdrawal_router.patch(
    "/withdrawal/destinations/{destination_id}",
    response_model=APIResponse[PayoutDestinationResponse],
    tags=DESTINATIONS,
)
async def update_destination(
    seller_id: DestinationSellerIdDep,
    destination_id: uuid.UUID,
    payload: PayoutDestinationUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Change the details. Past withdrawals keep what they were paid to."""
    return success_response(
        data=await service.update_destination(seller_id, destination_id, payload),
        message="Payout destination updated",
    )


@withdrawal_router.post(
    "/withdrawal/destinations/{destination_id}/activate",
    response_model=APIResponse[PayoutDestinationResponse],
    tags=DESTINATIONS,
)
async def activate_destination(
    seller_id: DestinationSellerIdDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    return success_response(
        data=await service.set_destination_active(seller_id, destination_id, active=True),
        message="Payout destination activated",
    )


@withdrawal_router.post(
    "/withdrawal/destinations/{destination_id}/deactivate",
    response_model=APIResponse[PayoutDestinationResponse],
    tags=DESTINATIONS,
)
async def deactivate_destination(
    seller_id: DestinationSellerIdDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Stop choosing this account for new withdrawals. Used ones are
    deactivated, never deleted."""
    return success_response(
        data=await service.set_destination_active(seller_id, destination_id, active=False),
        message="Payout destination deactivated",
    )


@withdrawal_router.delete(
    "/withdrawal/destinations/{destination_id}",
    response_model=APIResponse[None],
    tags=DESTINATIONS,
)
async def delete_destination(
    seller_id: DestinationSellerIdDep, destination_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Delete an account no withdrawal ever used. Deactivate any other."""
    await service.delete_destination(seller_id, destination_id)
    return success_response(message="Payout destination deleted")


# ── The seller: withdrawals ──────────────────────────────────────────────


@withdrawal_router.post(
    "/withdrawals",
    response_model=APIResponse[WithdrawalResponse],
    status_code=status.HTTP_201_CREATED,
    tags=WITHDRAWALS,
)
async def request_withdrawal(
    _: RequesterDep,
    seller: ActiveSellerDep,
    payload: WithdrawalRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Ask to be paid from your available balance to one of your saved
    payout destinations. The amount is reserved until staff decide."""
    withdrawal = await service.request_withdrawal(seller.id, payload)
    return success_response(
        data=withdrawal,
        message="Withdrawal requested. We will review it shortly.",
        status_code=status.HTTP_201_CREATED,
    )


@withdrawal_router.get(
    "/withdrawals/mine",
    response_model=APIResponse[Page[WithdrawalResponse]],
    tags=WITHDRAWALS,
)
async def list_my_withdrawals(
    seller_id: OwnSellerIdDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Your withdrawal requests, newest first."""
    return success_response(
        data=await service.list_my_withdrawals(seller_id, pagination),
        message="Withdrawals retrieved",
    )


@withdrawal_router.get(
    "/withdrawals/mine/{withdrawal_id}",
    response_model=APIResponse[WithdrawalResponse],
    tags=WITHDRAWALS,
)
async def get_my_withdrawal(
    seller_id: OwnSellerIdDep, withdrawal_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    return success_response(
        data=await service.get_my_withdrawal(seller_id, withdrawal_id),
        message="Withdrawal retrieved",
    )


@withdrawal_router.post(
    "/withdrawals/mine/{withdrawal_id}/cancel",
    response_model=APIResponse[WithdrawalResponse],
    tags=WITHDRAWALS,
)
async def cancel_withdrawal(
    seller_id: OwnSellerIdDep, withdrawal_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Call it off while it is still pending; the reserved funds go back."""
    return success_response(
        data=await service.cancel(seller_id, withdrawal_id), message="Withdrawal cancelled"
    )


# ── Staff: reviewing withdrawals ─────────────────────────────────────────


@withdrawal_router.get(
    "/withdrawals", response_model=APIResponse[Page[StaffWithdrawalResponse]], tags=WITHDRAWALS
)
async def list_withdrawals(
    _: ReviewerDep,
    pagination: PaginationDep,
    filters: Annotated[StaffWithdrawalFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every withdrawal, newest first. Use `status=pending` for the queue
    of requests to review."""
    return success_response(
        data=await service.list_withdrawals(pagination, filters), message="Withdrawals retrieved"
    )


@withdrawal_router.get(
    "/withdrawals/{withdrawal_id}",
    response_model=APIResponse[StaffWithdrawalResponse],
    tags=WITHDRAWALS,
)
async def get_withdrawal(
    _: ReviewerDep, withdrawal_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    return success_response(
        data=await service.get_withdrawal(withdrawal_id), message="Withdrawal retrieved"
    )


@withdrawal_router.post(
    "/withdrawals/{withdrawal_id}/approve",
    response_model=APIResponse[StaffWithdrawalResponse],
    tags=WITHDRAWALS,
)
async def approve_withdrawal(
    staff: ReviewerDep, withdrawal_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Accepted: pay the amount out by hand, then record the result. Safe
    to repeat."""
    withdrawal = await service.approve(withdrawal_id=withdrawal_id, staff_id=staff.id)
    return success_response(data=withdrawal, message="Withdrawal approved")


@withdrawal_router.post(
    "/withdrawals/{withdrawal_id}/reject",
    response_model=APIResponse[StaffWithdrawalResponse],
    tags=WITHDRAWALS,
)
async def reject_withdrawal(
    staff: ReviewerDep, withdrawal_id: uuid.UUID, payload: ReasonRequest, service: ServiceDep
) -> JSONResponse:
    """Declined. The seller sees the reason; the funds go back to them."""
    withdrawal = await service.reject(
        withdrawal_id=withdrawal_id, reason=payload.reason, staff_id=staff.id
    )
    return success_response(data=withdrawal, message="Withdrawal rejected")


@withdrawal_router.post(
    "/withdrawals/{withdrawal_id}/complete",
    response_model=APIResponse[StaffWithdrawalResponse],
    tags=WITHDRAWALS,
)
async def complete_withdrawal(
    staff: ReviewerDep,
    withdrawal_id: uuid.UUID,
    payload: CompleteRequest,
    service: ServiceDep,
) -> JSONResponse:
    """The money reached the seller. Record it, with the payout reference
    if you have one."""
    withdrawal = await service.complete(
        withdrawal_id=withdrawal_id, payout_reference=payload.payout_reference, staff_id=staff.id
    )
    return success_response(data=withdrawal, message="Withdrawal completed")


@withdrawal_router.post(
    "/withdrawals/{withdrawal_id}/fail",
    response_model=APIResponse[StaffWithdrawalResponse],
    tags=WITHDRAWALS,
)
async def fail_withdrawal(
    staff: ReviewerDep, withdrawal_id: uuid.UUID, payload: ReasonRequest, service: ServiceDep
) -> JSONResponse:
    """The payout did not go through; the funds go back to the seller."""
    withdrawal = await service.fail(
        withdrawal_id=withdrawal_id, reason=payload.reason, staff_id=staff.id
    )
    return success_response(data=withdrawal, message="Withdrawal failed")
