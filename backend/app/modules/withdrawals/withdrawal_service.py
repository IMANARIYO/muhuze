"""Withdrawal requests and payout destinations.

Rules are documented in docs/features/018_withdrawals.md and README §13.8.

The money side lives in the wallet ledger: this service decides WHAT happens
(request, cancel, approve, reject, complete, fail) and the ledger does it
under a row lock, inside the same transaction. The ledger's movements do not
commit on their own (AGENTS.md §13): every public method here is one unit of
work and commits it, so a request, its wallet movement, and its status all
succeed or fail together.

    request   reserve the amount out of AVAILABLE     (funds cannot be spent twice)
    cancel / reject / fail   release it back           (a NEW movement, never an edit)
    complete  count it in total_withdrawn             (balances do not move)

A payout happens OUTSIDE the system (README §20 W6, W8): staff transfer the
money by hand and then record what they did here.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.wallets.wallet_service import WalletService
from app.modules.withdrawals.withdrawal_constants import (
    DEFAULT_CURRENCY,
    MINIMUM_AMOUNT,
    WithdrawalStatus,
)
from app.modules.withdrawals.withdrawal_exceptions import (
    AmountBelowMinimumError,
    PayoutDestinationInUseError,
    PayoutDestinationNotActiveError,
    PayoutDestinationNotFoundError,
    WithdrawalNotFoundError,
    WithdrawalStatusConflictError,
)
from app.modules.withdrawals.withdrawal_model import SellerPayoutDestination, Withdrawal
from app.modules.withdrawals.withdrawal_repository import WithdrawalRepository
from app.modules.withdrawals.withdrawal_schema import (
    PayoutDestinationCreateRequest,
    PayoutDestinationResponse,
    PayoutDestinationUpdateRequest,
    StaffWithdrawalFilters,
    StaffWithdrawalResponse,
    WithdrawalRequest,
    WithdrawalResponse,
)
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

Status = WithdrawalStatus


class WithdrawalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = WithdrawalRepository(session)
        # Same session: the ledger's movements commit (or roll back) with
        # this service's transaction (AGENTS.md §7, §13).
        self._wallet = WalletService(session)

    # ── Payout destinations (the seller's own) ───────────────────────────

    async def list_destinations(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[PayoutDestinationResponse]:
        rows, total = await self._repository.list_destinations(seller_id, pagination)
        items = [PayoutDestinationResponse.model_validate(row) for row in rows]
        return Page[PayoutDestinationResponse].build(items, total, pagination)

    async def create_destination(
        self, seller_id: uuid.UUID, payload: PayoutDestinationCreateRequest
    ) -> PayoutDestinationResponse:
        destination = SellerPayoutDestination(
            seller_id=seller_id,
            type=payload.type.value,
            provider=payload.provider,
            account_number=payload.account_number,
            account_name=payload.account_name,
        )
        await self._repository.add(destination)
        await self._session.commit()
        logger.info("payout destination created", extra={"seller_id": str(seller_id)})
        return PayoutDestinationResponse.model_validate(destination)

    async def update_destination(
        self,
        seller_id: uuid.UUID,
        destination_id: uuid.UUID,
        payload: PayoutDestinationUpdateRequest,
    ) -> PayoutDestinationResponse:
        destination = await self._own_destination(seller_id, destination_id)
        if payload.type is not None:
            destination.type = payload.type.value
        if payload.provider is not None:
            destination.provider = payload.provider
        if payload.account_number is not None:
            destination.account_number = payload.account_number
        if payload.account_name is not None:
            destination.account_name = payload.account_name
        await self._session.commit()
        return PayoutDestinationResponse.model_validate(destination)

    async def set_destination_active(
        self, seller_id: uuid.UUID, destination_id: uuid.UUID, *, active: bool
    ) -> PayoutDestinationResponse:
        destination = await self._own_destination(seller_id, destination_id, for_update=True)
        destination.is_active = active
        await self._session.commit()
        return PayoutDestinationResponse.model_validate(destination)

    async def delete_destination(self, seller_id: uuid.UUID, destination_id: uuid.UUID) -> None:
        """Delete a destination no withdrawal ever used. A used one is
        deactivated, never deleted (README §14, invariant 22)."""
        destination = await self._own_destination(seller_id, destination_id, for_update=True)
        if await self._repository.destination_is_used(destination.id):
            raise PayoutDestinationInUseError()
        await self._repository.delete(destination)
        await self._session.commit()

    # ── The seller's withdrawals ─────────────────────────────────────────

    async def request_withdrawal(
        self, seller_id: uuid.UUID, payload: WithdrawalRequest
    ) -> WithdrawalResponse:
        """Ask to be paid from the available balance. The amount is reserved
        in the same transaction, so it cannot be spent twice."""
        destination = await self._own_destination(
            seller_id, payload.payout_destination_id, for_update=True
        )
        if not destination.is_active:
            raise PayoutDestinationNotActiveError()
        if payload.amount < MINIMUM_AMOUNT:
            raise AmountBelowMinimumError()

        withdrawal = Withdrawal(
            seller_id=seller_id,
            payout_destination_id=destination.id,
            amount=payload.amount,
            currency=DEFAULT_CURRENCY,
            status=Status.PENDING.value,
            # Snapshot: later edits to the destination never rewrite this.
            destination_type=destination.type,
            destination_provider=destination.provider,
            destination_account_number=destination.account_number,
            destination_account_name=destination.account_name,
        )
        await self._repository.add(withdrawal)
        await self._wallet.reserve_for_withdrawal(
            withdrawal.id, seller_id, payload.amount, DEFAULT_CURRENCY
        )
        await self._session.commit()
        logger.info(
            "withdrawal requested",
            extra={"withdrawal_id": str(withdrawal.id), "seller_id": str(seller_id)},
        )
        return WithdrawalResponse.model_validate(withdrawal)

    async def list_my_withdrawals(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[WithdrawalResponse]:
        rows, total = await self._repository.list_for_seller(seller_id, pagination)
        items = [WithdrawalResponse.model_validate(row) for row in rows]
        return Page[WithdrawalResponse].build(items, total, pagination)

    async def get_my_withdrawal(
        self, seller_id: uuid.UUID, withdrawal_id: uuid.UUID
    ) -> WithdrawalResponse:
        return WithdrawalResponse.model_validate(
            await self._own_withdrawal(seller_id, withdrawal_id)
        )

    async def cancel(self, seller_id: uuid.UUID, withdrawal_id: uuid.UUID) -> WithdrawalResponse:
        """The seller changes their mind while it is still pending. The
        reserved funds come back with a new movement."""
        withdrawal = await self._own_withdrawal(seller_id, withdrawal_id, for_update=True)
        if withdrawal.status == Status.CANCELLED.value:
            return WithdrawalResponse.model_validate(withdrawal)  # repeating changes nothing
        if withdrawal.status != Status.PENDING.value:
            raise WithdrawalStatusConflictError()
        withdrawal.status = Status.CANCELLED.value
        await self._wallet.release_withdrawal(
            withdrawal.id, seller_id, withdrawal.amount, withdrawal.currency
        )
        await self._session.commit()
        logger.info("withdrawal cancelled", extra={"withdrawal_id": str(withdrawal.id)})
        return WithdrawalResponse.model_validate(withdrawal)

    # ── Staff: reviewing ─────────────────────────────────────────────────

    async def list_withdrawals(
        self, pagination: PaginationParams, filters: StaffWithdrawalFilters
    ) -> Page[StaffWithdrawalResponse]:
        rows, total = await self._repository.list_withdrawals(
            pagination,
            status=filters.status.value if filters.status is not None else None,
            seller_id=filters.seller_id,
        )
        items = [StaffWithdrawalResponse.model_validate(row) for row in rows]
        return Page[StaffWithdrawalResponse].build(items, total, pagination)

    async def get_withdrawal(self, withdrawal_id: uuid.UUID) -> StaffWithdrawalResponse:
        withdrawal = await self._staff_withdrawal(withdrawal_id)
        return StaffWithdrawalResponse.model_validate(withdrawal)

    async def approve(
        self, withdrawal_id: uuid.UUID, *, staff_id: uuid.UUID
    ) -> StaffWithdrawalResponse:
        """The request is accepted: staff now pay it out by hand. The funds
        stay reserved until it completes or fails."""
        withdrawal = await self._staff_withdrawal(withdrawal_id, for_update=True)
        if withdrawal.status == Status.PROCESSING.value:
            return StaffWithdrawalResponse.model_validate(withdrawal)  # repeating changes nothing
        if withdrawal.status != Status.PENDING.value:
            raise WithdrawalStatusConflictError()
        withdrawal.status = Status.PROCESSING.value
        withdrawal.reviewed_by_account_id = staff_id
        withdrawal.reviewed_at = utc_now()
        await self._session.commit()
        logger.info("withdrawal approved", extra={"withdrawal_id": str(withdrawal.id)})
        return StaffWithdrawalResponse.model_validate(withdrawal)

    async def reject(
        self, withdrawal_id: uuid.UUID, *, reason: str, staff_id: uuid.UUID
    ) -> StaffWithdrawalResponse:
        """The request is declined; the reserved funds go back to the seller."""
        withdrawal = await self._staff_withdrawal(withdrawal_id, for_update=True)
        if withdrawal.status == Status.REJECTED.value:
            return StaffWithdrawalResponse.model_validate(withdrawal)
        if withdrawal.status != Status.PENDING.value:
            raise WithdrawalStatusConflictError()
        withdrawal.status = Status.REJECTED.value
        withdrawal.reason = reason
        withdrawal.reviewed_by_account_id = staff_id
        withdrawal.reviewed_at = utc_now()
        await self._wallet.release_withdrawal(
            withdrawal.id, withdrawal.seller_id, withdrawal.amount, withdrawal.currency
        )
        await self._session.commit()
        logger.info("withdrawal rejected", extra={"withdrawal_id": str(withdrawal.id)})
        return StaffWithdrawalResponse.model_validate(withdrawal)

    async def complete(
        self, withdrawal_id: uuid.UUID, *, payout_reference: str | None, staff_id: uuid.UUID
    ) -> StaffWithdrawalResponse:
        """The money reached the seller: the payout is recorded and counted
        in total_withdrawn. The balances were already reduced at request."""
        withdrawal = await self._staff_withdrawal(withdrawal_id, for_update=True)
        if withdrawal.status == Status.COMPLETED.value:
            return StaffWithdrawalResponse.model_validate(withdrawal)
        if withdrawal.status != Status.PROCESSING.value:
            raise WithdrawalStatusConflictError()
        withdrawal.status = Status.COMPLETED.value
        withdrawal.payout_reference = payout_reference
        withdrawal.completed_at = utc_now()
        await self._wallet.complete_withdrawal(
            withdrawal.id, withdrawal.seller_id, withdrawal.amount, withdrawal.currency
        )
        await self._session.commit()
        logger.info("withdrawal completed", extra={"withdrawal_id": str(withdrawal.id)})
        return StaffWithdrawalResponse.model_validate(withdrawal)

    async def fail(
        self, withdrawal_id: uuid.UUID, *, reason: str, staff_id: uuid.UUID
    ) -> StaffWithdrawalResponse:
        """The payout did not go through; the reserved funds go back."""
        withdrawal = await self._staff_withdrawal(withdrawal_id, for_update=True)
        if withdrawal.status == Status.FAILED.value:
            return StaffWithdrawalResponse.model_validate(withdrawal)
        if withdrawal.status != Status.PROCESSING.value:
            raise WithdrawalStatusConflictError()
        withdrawal.status = Status.FAILED.value
        withdrawal.reason = reason
        withdrawal.reviewed_by_account_id = withdrawal.reviewed_by_account_id or staff_id
        withdrawal.reviewed_at = withdrawal.reviewed_at or utc_now()
        await self._wallet.release_withdrawal(
            withdrawal.id, withdrawal.seller_id, withdrawal.amount, withdrawal.currency
        )
        await self._session.commit()
        logger.info("withdrawal failed", extra={"withdrawal_id": str(withdrawal.id)})
        return StaffWithdrawalResponse.model_validate(withdrawal)

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _own_destination(
        self, seller_id: uuid.UUID, destination_id: uuid.UUID, *, for_update: bool = False
    ) -> SellerPayoutDestination:
        destination = await self._repository.get_destination(
            seller_id, destination_id, for_update=for_update
        )
        if destination is None:
            raise PayoutDestinationNotFoundError()
        return destination

    async def _own_withdrawal(
        self, seller_id: uuid.UUID, withdrawal_id: uuid.UUID, *, for_update: bool = False
    ) -> Withdrawal:
        withdrawal = await self._repository.get_withdrawal_for_seller(
            seller_id, withdrawal_id, for_update=for_update
        )
        if withdrawal is None:
            raise WithdrawalNotFoundError()
        return withdrawal

    async def _staff_withdrawal(
        self, withdrawal_id: uuid.UUID, *, for_update: bool = False
    ) -> Withdrawal:
        withdrawal = await self._repository.get_withdrawal(withdrawal_id, for_update=for_update)
        if withdrawal is None:
            raise WithdrawalNotFoundError()
        return withdrawal
