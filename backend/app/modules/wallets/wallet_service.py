"""Revenue records and seller wallets: what happens to the money once a
payment is confirmed.
Rules are documented in docs/features/012_wallets.md and README §13, §14.

The buyer paid MUHUZE. MUHUZE now owes each seller their share. A wallet is
that debt: a record inside MUHUZE, not money in the seller's hands. Money
reaches a seller only through a withdrawal.

    record_earning   a paid sale            + pending
    settle           the buyer has it       pending → available
    reverse          a paid sale undone     − pending
    reserve          a withdrawal asked     − available
    release          it did not happen      + available

Those five are the ONLY ways a balance moves. The first three are called by
the orders feature, the last two by the withdrawals feature, inside ITS
transaction (they do not commit), so a request, its wallet movement, and its
status all succeed or fail together. Each is idempotent: called twice, it
acts once.

Balances are never set directly. Every change writes a WalletTransaction
holding the change and the balances after it.
"""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.wallets.wallet_constants import WalletTransactionKind
from app.modules.wallets.wallet_exceptions import (
    EarningAlreadySettledError,
    EarningNotRecordedError,
    EarningReversedError,
    InsufficientAvailableBalanceError,
    WalletNotFoundError,
)
from app.modules.wallets.wallet_model import RevenueTransaction, Wallet, WalletTransaction
from app.modules.wallets.wallet_repository import WalletRepository
from app.modules.wallets.wallet_schema import (
    RevenueFilters,
    RevenueSummaryResponse,
    RevenueTransactionResponse,
    WalletResponse,
    WalletTransactionResponse,
)
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

ZERO = Decimal("0.00")
Kind = WalletTransactionKind


class WalletService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = WalletRepository(session)

    # ── The ledger: called by orders, inside its transaction (no commit) ──

    async def record_earning(
        self,
        *,
        seller_order_id: uuid.UUID,
        order_id: uuid.UUID,
        seller_id: uuid.UUID,
        gross_amount: Decimal,
        commission_rate: Decimal,
        commission_amount: Decimal,
        seller_amount: Decimal,
        currency: str,
    ) -> None:
        """A seller order has been paid: record the sale's revenue split, and
        credit the seller's share to their PENDING balance.

        The amounts are the ones frozen on the seller order when it was
        placed; nothing is recalculated here (README §11.1).
        """
        if await self._repository.get_revenue_for_seller_order(seller_order_id) is not None:
            return  # already recorded: a repeated confirmation changes nothing
        revenue = RevenueTransaction(
            seller_order_id=seller_order_id,
            order_id=order_id,
            seller_id=seller_id,
            gross_amount=gross_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            seller_amount=seller_amount,
            currency=currency,
        )
        await self._repository.add(revenue)
        wallet = await self._repository.lock_wallet(seller_id, currency)
        wallet.total_earned += seller_amount
        await self._record(wallet, Kind.EARNING, pending=seller_amount, revenue=revenue)

    async def settle(self, seller_order_id: uuid.UUID) -> None:
        """The buyer confirmed receipt: the seller's share for this order
        moves from pending to AVAILABLE and can be withdrawn. The single
        settlement rule (README §13.6)."""
        revenue = await self._revenue(seller_order_id)
        if revenue.reversed_at is not None:
            raise EarningReversedError()
        if await self._repository.has_transaction(revenue.id, Kind.SETTLEMENT.value):
            return
        wallet = await self._repository.lock_wallet(revenue.seller_id, revenue.currency)
        await self._record(
            wallet,
            Kind.SETTLEMENT,
            pending=-revenue.seller_amount,
            available=revenue.seller_amount,
            revenue=revenue,
        )

    async def reverse(self, seller_order_id: uuid.UUID) -> None:
        """A paid sale was undone (the seller rejected it): take the earning
        back out of pending. The original records stay; this writes a new,
        reversing one (README §13.7). Refunding the buyer is not done here."""
        revenue = await self._revenue(seller_order_id)
        if revenue.reversed_at is not None:
            return
        if await self._repository.has_transaction(revenue.id, Kind.SETTLEMENT.value):
            raise EarningAlreadySettledError()
        wallet = await self._repository.lock_wallet(revenue.seller_id, revenue.currency)
        wallet.total_earned -= revenue.seller_amount
        revenue.reversed_at = utc_now()
        await self._record(wallet, Kind.REVERSAL, pending=-revenue.seller_amount, revenue=revenue)

    # ── Withdrawals: called by the withdrawals feature, inside its
    # ── transaction (no commit) ─────────────────────────────────────────

    async def reserve_for_withdrawal(
        self, withdrawal_id: uuid.UUID, seller_id: uuid.UUID, amount: Decimal, currency: str
    ) -> None:
        """A withdrawal has been requested: take the amount out of the
        AVAILABLE balance so the same funds cannot be spent twice. The
        balance is checked under the wallet lock, so two requests cannot
        both pass (README §14, invariant 10)."""
        if await self._repository.has_withdrawal_transaction(withdrawal_id, Kind.WITHDRAWAL.value):
            return
        wallet = await self._repository.lock_wallet(seller_id, currency)
        if wallet.available_balance < amount:
            raise InsufficientAvailableBalanceError()
        await self._record(wallet, Kind.WITHDRAWAL, available=-amount, withdrawal_id=withdrawal_id)

    async def release_withdrawal(
        self, withdrawal_id: uuid.UUID, seller_id: uuid.UUID, amount: Decimal, currency: str
    ) -> None:
        """A withdrawal was rejected, failed, or cancelled: give the reserved
        funds back with a NEW movement. The original reserve is never edited
        (README §14, invariant 12)."""
        if await self._repository.has_withdrawal_transaction(
            withdrawal_id, Kind.WITHDRAWAL_RELEASE.value
        ):
            return
        wallet = await self._repository.lock_wallet(seller_id, currency)
        await self._record(
            wallet, Kind.WITHDRAWAL_RELEASE, available=amount, withdrawal_id=withdrawal_id
        )

    async def complete_withdrawal(
        self, withdrawal_id: uuid.UUID, seller_id: uuid.UUID, amount: Decimal, currency: str
    ) -> None:
        """The payout reached the seller: count it in the running total. The
        balances do not move — the funds were already reserved. A zero-change
        movement records it, so a repeated call cannot count it twice."""
        if await self._repository.has_withdrawal_transaction(
            withdrawal_id, Kind.WITHDRAWAL_COMPLETE.value
        ):
            return
        wallet = await self._repository.lock_wallet(seller_id, currency)
        wallet.total_withdrawn += amount
        await self._record(
            wallet, Kind.WITHDRAWAL_COMPLETE, available=ZERO, withdrawal_id=withdrawal_id
        )

    # ── Reading ──────────────────────────────────────────────────────────

    async def get_wallet(self, seller_id: uuid.UUID) -> WalletResponse:
        """A seller's balances. A seller who has not earned yet has no wallet
        row; they are shown zeros rather than an error."""
        wallet = await self._repository.get_wallet(seller_id)
        if wallet is None:
            return WalletResponse(
                seller_id=seller_id,
                currency="RWF",
                pending_balance=ZERO,
                available_balance=ZERO,
                total_earned=ZERO,
                total_withdrawn=ZERO,
            )
        return WalletResponse(
            seller_id=wallet.seller_id,
            currency=wallet.currency,
            pending_balance=wallet.pending_balance,
            available_balance=wallet.available_balance,
            total_earned=wallet.total_earned,
            total_withdrawn=wallet.total_withdrawn,
        )

    async def list_transactions(
        self, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[WalletTransactionResponse]:
        wallet = await self._repository.get_wallet(seller_id)
        if wallet is None:
            return Page[WalletTransactionResponse].build([], 0, pagination)
        rows, total = await self._repository.list_transactions(wallet.id, pagination)
        items = [
            WalletTransactionResponse(
                id=movement.id,
                kind=movement.kind,
                pending_change=movement.pending_change,
                available_change=movement.available_change,
                pending_after=movement.pending_after,
                available_after=movement.available_after,
                order_id=revenue.order_id if revenue is not None else None,
                seller_order_id=revenue.seller_order_id if revenue is not None else None,
                withdrawal_id=movement.withdrawal_id,
                created_at=movement.created_at,
            )
            for movement, revenue in rows
        ]
        return Page[WalletTransactionResponse].build(items, total, pagination)

    async def reconcile(self, seller_id: uuid.UUID) -> bool:
        """True if the wallet's balances equal the sum of its movements
        (README §14, invariant 8). They always should."""
        wallet = await self._repository.get_wallet(seller_id)
        if wallet is None:
            raise WalletNotFoundError()
        pending, available = await self._repository.sum_transactions(wallet.id)
        return (wallet.pending_balance, wallet.available_balance) == (pending, available)

    async def list_revenue(
        self, pagination: PaginationParams, filters: RevenueFilters
    ) -> Page[RevenueTransactionResponse]:
        rows, total = await self._repository.list_revenue(
            pagination, seller_id=filters.seller_id, order_id=filters.order_id
        )
        items = [RevenueTransactionResponse.model_validate(row) for row in rows]
        return Page[RevenueTransactionResponse].build(items, total, pagination)

    async def summarize_revenue(self, filters: RevenueFilters) -> RevenueSummaryResponse:
        sales, gross, commission, seller = await self._repository.summarize_revenue(
            seller_id=filters.seller_id
        )
        return RevenueSummaryResponse(
            sales=sales,
            # Always two decimal places, also when there is nothing to add up.
            gross_amount=Decimal(gross).quantize(ZERO),
            commission_amount=Decimal(commission).quantize(ZERO),
            seller_amount=Decimal(seller).quantize(ZERO),
            currency="RWF",
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _revenue(self, seller_order_id: uuid.UUID) -> RevenueTransaction:
        revenue = await self._repository.get_revenue_for_seller_order(
            seller_order_id, for_update=True
        )
        if revenue is None:
            raise EarningNotRecordedError()
        return revenue

    async def _record(
        self,
        wallet: Wallet,
        kind: WalletTransactionKind,
        *,
        pending: Decimal = ZERO,
        available: Decimal = ZERO,
        revenue: RevenueTransaction | None = None,
        withdrawal_id: uuid.UUID | None = None,
    ) -> None:
        """Write one movement and apply it to the locked wallet. The ONLY
        code that changes a balance. Exactly one of `revenue` /
        `withdrawal_id` is set (the database enforces it)."""
        wallet.pending_balance += pending
        wallet.available_balance += available
        await self._repository.add(
            WalletTransaction(
                wallet_id=wallet.id,
                kind=kind.value,
                pending_change=pending,
                available_change=available,
                pending_after=wallet.pending_balance,
                available_after=wallet.available_balance,
                revenue_transaction_id=revenue.id if revenue is not None else None,
                withdrawal_id=withdrawal_id,
            )
        )
        logger.info(
            "wallet movement recorded",
            extra={
                "kind": kind.value,
                "seller_id": str(wallet.seller_id),
                **(
                    {"seller_order_id": str(revenue.seller_order_id)}
                    if revenue is not None
                    else {"withdrawal_id": str(withdrawal_id)}
                ),
            },
        )
