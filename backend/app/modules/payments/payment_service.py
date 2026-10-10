"""Payments: how the buyer's money reaches MUHUZE, and how MUHUZE knows it did.
Rules are documented in docs/features/011_payments.md and README §12.

This is Phase 1: the buyer pays MUHUZE outside the app and submits the
transaction reference; staff check MUHUZE's real statement and approve.

`confirm_payment` is the ONLY way a payment becomes paid. An online gateway
(Phase 2) will call the same function after verifying its own confirmation;
nothing downstream will know the difference. It is idempotent, and its whole
effect (the payment paid, the order released to its sellers) is one
transaction.

The buyer always pays MUHUZE, never a seller.
Every public method is one unit of work and commits it.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.orders.order_model import Order
from app.modules.orders.order_service import OrderService
from app.modules.payments.payment_constants import (
    DEFAULT_CURRENCY,
    PaymentChannel,
    PaymentPurpose,
    PaymentStatus,
)
from app.modules.payments.payment_exceptions import (
    InactiveDefaultDestinationError,
    OrderNotPayableError,
    OwnPaymentVerificationError,
    PaymentAlreadySubmittedError,
    PaymentAmountMismatchError,
    PaymentDestinationInUseError,
    PaymentDestinationNotFoundError,
    PaymentDestinationUnavailableError,
    PaymentNotFoundError,
    PaymentReferenceUsedError,
    PaymentStatusConflictError,
)
from app.modules.payments.payment_model import Payment, PaymentDestination
from app.modules.payments.payment_repository import PaymentRepository
from app.modules.payments.payment_schema import (
    PaymentDestinationCreateRequest,
    PaymentDestinationResponse,
    PaymentDestinationUpdateRequest,
    PaymentInstructionsResponse,
    PaymentResponse,
    PaymentSubmitRequest,
    PayToResponse,
    StaffPaymentFilters,
    StaffPaymentResponse,
)
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

REFERENCE_INDEX = "uq_payments_reference_lower"


class PaymentService:
    def __init__(self, session: AsyncSession, order_service: OrderService) -> None:
        self._session = session
        self._orders = order_service
        self._repository = PaymentRepository(session)

    # ── The single confirmation path ─────────────────────────────────────

    async def confirm_payment(
        self, payment_id: uuid.UUID, *, verified_by: uuid.UUID | None
    ) -> Payment:
        """Mark a payment as paid and release its order to the sellers.

        The ONE function through which a payment becomes paid, whoever or
        whatever verified it (README §12.1). `verified_by` is the member of
        staff for a manual payment, or None when a gateway confirmed it.

        Idempotent: confirming a payment that is already paid changes nothing
        and creates nothing twice (README §12.8). The payment row is locked,
        the order's own "paid" step is idempotent too, and the database allows
        only one paid payment per order.
        """
        payment = await self._repository.get_payment(payment_id, for_update=True)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.status == PaymentStatus.PAID:
            return payment
        if payment.status != PaymentStatus.AWAITING_VERIFICATION:
            raise PaymentStatusConflictError("Only a payment awaiting verification can be approved")

        now = utc_now()
        payment.status = PaymentStatus.PAID.value
        payment.verified_by_account_id = verified_by
        payment.verified_at = now
        payment.paid_at = now
        try:
            # Raises if the order was cancelled meanwhile; nothing is saved then.
            order = await self._orders.mark_paid(payment.order_id)
            if (order.total_amount, order.currency) != (payment.amount, payment.currency):
                raise PaymentAmountMismatchError()
            await self._session.commit()
        except IntegrityError as exc:
            # Another payment for this order was confirmed first.
            await self._session.rollback()
            raise PaymentStatusConflictError("This order has already been paid") from exc
        logger.info(
            "payment confirmed",
            extra={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "channel": payment.channel,
                "by_account_id": str(verified_by) if verified_by else None,
            },
        )
        return payment

    # ── The buyer ────────────────────────────────────────────────────────

    async def get_instructions(
        self, *, buyer_account_id: uuid.UUID, order_id: uuid.UUID
    ) -> PaymentInstructionsResponse:
        """How to pay for one of the buyer's own orders, and what they have
        submitted so far. MUHUZE's accounts are shown only while the order is
        actually waiting for payment (README §12.3)."""
        order = await self._orders.get_order_of_buyer(
            buyer_account_id=buyer_account_id, order_id=order_id
        )
        attempts = await self._repository.list_for_order(order.id)
        awaiting_payment = _awaits_payment(order)
        destinations = (
            await self._repository.list_active_destinations(order.currency)
            if awaiting_payment
            else []
        )
        return PaymentInstructionsResponse(
            order_id=order.id,
            order_number=order.order_number,
            amount=order.total_amount,
            currency=order.currency,
            can_pay=awaiting_payment
            and bool(destinations)
            and not any(a.status == PaymentStatus.AWAITING_VERIFICATION for a in attempts),
            pay_to=[PayToResponse.model_validate(destination) for destination in destinations],
            attempts=[PaymentResponse.model_validate(attempt) for attempt in attempts],
        )

    async def submit_payment(
        self, *, buyer_account_id: uuid.UUID, order_id: uuid.UUID, payload: PaymentSubmitRequest
    ) -> PaymentResponse:
        """The buyer says "I have paid": which account, and the transaction
        reference. Nothing is paid yet; it waits for staff to check."""
        order = await self._orders.get_order_of_buyer(
            buyer_account_id=buyer_account_id, order_id=order_id
        )
        if not _awaits_payment(order):
            raise OrderNotPayableError()
        destination = await self._repository.get_destination(payload.destination_id)
        if (
            destination is None
            or not destination.is_active
            or destination.currency != order.currency
        ):
            raise PaymentDestinationUnavailableError()
        attempts = await self._repository.list_for_order(order.id)
        if any(a.status == PaymentStatus.AWAITING_VERIFICATION for a in attempts):
            raise PaymentAlreadySubmittedError()

        payment = Payment(
            purpose=PaymentPurpose.ORDER.value,
            order_id=order.id,
            order_number=order.order_number,
            payer_account_id=buyer_account_id,
            # Always the full order total: there are no part payments.
            amount=order.total_amount,
            currency=order.currency,
            channel=PaymentChannel.MANUAL.value,
            status=PaymentStatus.AWAITING_VERIFICATION.value,
            destination_id=destination.id,
            destination_method=destination.method,
            destination_provider=destination.provider,
            destination_account_reference=destination.account_reference,
            destination_registered_name=destination.registered_name,
            reference=payload.reference,
            payer_name=payload.payer_name,
            payer_phone=payload.payer_phone,
        )
        try:
            await self._repository.add_payment(payment)
        except IntegrityError as exc:
            await self._session.rollback()
            if REFERENCE_INDEX in str(exc.orig):
                raise PaymentReferenceUsedError() from exc
            # Lost a race with another submission for the same order.
            raise PaymentAlreadySubmittedError() from exc
        await self._session.commit()
        logger.info(
            "payment submitted",
            extra={"payment_id": str(payment.id), "order_id": str(order.id)},
        )
        return PaymentResponse.model_validate(payment)

    # ── Staff: verifying payments ────────────────────────────────────────

    async def list_payments(
        self, pagination: PaginationParams, filters: StaffPaymentFilters
    ) -> Page[StaffPaymentResponse]:
        payments, total = await self._repository.list_payments(
            pagination,
            status=filters.status.value if filters.status else None,
            search=filters.q.strip() or None if filters.q else None,
        )
        items = [StaffPaymentResponse.model_validate(payment) for payment in payments]
        return Page[StaffPaymentResponse].build(items, total, pagination)

    async def get_payment(self, payment_id: uuid.UUID) -> StaffPaymentResponse:
        payment = await self._repository.get_payment(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        return StaffPaymentResponse.model_validate(payment)

    async def approve(
        self, *, payment_id: uuid.UUID, approved_by: uuid.UUID
    ) -> StaffPaymentResponse:
        """Staff confirm, having checked MUHUZE's statement, that the money
        arrived. Goes through `confirm_payment`, like every confirmation."""
        payment = await self._repository.get_payment(payment_id)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.payer_account_id == approved_by:
            raise OwnPaymentVerificationError()
        confirmed = await self.confirm_payment(payment_id, verified_by=approved_by)
        return StaffPaymentResponse.model_validate(confirmed)

    async def reject(
        self, *, payment_id: uuid.UUID, reason: str, rejected_by: uuid.UUID
    ) -> StaffPaymentResponse:
        """The reference did not check out. The buyer sees why and can submit
        again; this attempt is kept as a record."""
        payment = await self._repository.get_payment(payment_id, for_update=True)
        if payment is None:
            raise PaymentNotFoundError()
        if payment.payer_account_id == rejected_by:
            raise OwnPaymentVerificationError()
        if payment.status != PaymentStatus.AWAITING_VERIFICATION:
            raise PaymentStatusConflictError("Only a payment awaiting verification can be rejected")
        payment.status = PaymentStatus.REJECTED.value
        payment.rejection_reason = reason
        payment.verified_by_account_id = rejected_by
        payment.verified_at = utc_now()
        await self._session.commit()
        logger.info(
            "payment rejected",
            extra={"payment_id": str(payment.id), "by_account_id": str(rejected_by)},
        )
        return StaffPaymentResponse.model_validate(payment)

    # ── Staff: MUHUZE's receiving accounts ───────────────────────────────

    async def list_destinations(
        self, pagination: PaginationParams
    ) -> Page[PaymentDestinationResponse]:
        destinations, total = await self._repository.list_destinations(pagination)
        items = [PaymentDestinationResponse.model_validate(d) for d in destinations]
        return Page[PaymentDestinationResponse].build(items, total, pagination)

    async def create_destination(
        self, *, payload: PaymentDestinationCreateRequest, created_by: uuid.UUID
    ) -> PaymentDestination:
        destination = PaymentDestination(
            method=payload.method.value,
            currency=DEFAULT_CURRENCY,
            provider=payload.provider,
            account_reference=payload.account_reference,
            registered_name=payload.registered_name,
            instructions=payload.instructions or None,
            is_default=payload.is_default,
            created_by_account_id=created_by,
        )
        if payload.is_default:
            await self._repository.clear_default(destination.currency)
        await self._repository.add_destination(destination)
        await self._session.commit()
        self._log_destination("payment destination created", destination, created_by)
        return destination

    async def update_destination(
        self,
        destination_id: uuid.UUID,
        *,
        payload: PaymentDestinationUpdateRequest,
        updated_by: uuid.UUID,
    ) -> PaymentDestination:
        """Change where buyers are told to pay. Payments already submitted
        keep the details they were made to."""
        destination = await self._destination(destination_id)
        changes = payload.model_dump(mode="json", exclude_unset=True)
        if "instructions" in changes:
            changes["instructions"] = changes["instructions"] or None
        for field, value in changes.items():
            setattr(destination, field, value)
        await self._session.commit()
        self._log_destination("payment destination updated", destination, updated_by)
        return destination

    async def set_destination_active(
        self, destination_id: uuid.UUID, *, active: bool, changed_by: uuid.UUID
    ) -> PaymentDestination:
        destination = await self._destination(destination_id)
        destination.is_active = active
        if not active:
            # An inactive destination can never be the default.
            destination.is_default = False
        await self._session.commit()
        self._log_destination("payment destination status changed", destination, changed_by)
        return destination

    async def set_default_destination(
        self, destination_id: uuid.UUID, *, changed_by: uuid.UUID
    ) -> PaymentDestination:
        destination = await self._destination(destination_id)
        if not destination.is_active:
            raise InactiveDefaultDestinationError()
        if not destination.is_default:
            await self._repository.clear_default(destination.currency)
            destination.is_default = True
        await self._session.commit()
        self._log_destination("payment destination set as default", destination, changed_by)
        return destination

    async def delete_destination(self, destination_id: uuid.UUID, *, deleted_by: uuid.UUID) -> None:
        """Delete a destination no payment ever used. Otherwise deactivate it."""
        destination = await self._destination(destination_id)
        try:
            await self._repository.delete_destination(destination)
        except IntegrityError as exc:
            await self._session.rollback()
            raise PaymentDestinationInUseError() from exc
        await self._session.commit()
        logger.info(
            "payment destination deleted",
            extra={"destination_id": str(destination_id), "by_account_id": str(deleted_by)},
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _destination(self, destination_id: uuid.UUID) -> PaymentDestination:
        destination = await self._repository.get_destination(destination_id)
        if destination is None:
            raise PaymentDestinationNotFoundError()
        return destination

    @staticmethod
    def _log_destination(message: str, destination: PaymentDestination, by: uuid.UUID) -> None:
        # The id only: account numbers and names are never written to logs.
        logger.info(
            message,
            extra={
                "destination_id": str(destination.id),
                "is_active": destination.is_active,
                "is_default": destination.is_default,
                "by_account_id": str(by),
            },
        )


def _awaits_payment(order: Order) -> bool:
    return order.paid_at is None and order.cancelled_at is None
