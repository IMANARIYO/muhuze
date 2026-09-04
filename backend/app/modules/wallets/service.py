import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.revenue.repository import RevenueTransactionRepository
from app.modules.wallets.exceptions import (
    InsufficientWalletBalanceError,
    InvalidWithdrawalStatusError,
    WalletNotFoundError,
    WithdrawalNotFoundError,
)
from app.modules.wallets.models import (
    Wallet,
    WalletTransaction,
    WalletTransactionStatus,
    WithdrawalRequest,
    WithdrawalStatus,
)
from app.modules.wallets.repository import (
    WalletRepository,
    WalletTransactionRepository,
    WithdrawalRequestRepository,
)


class WalletService:
    """Reconcile and operate a seller's wallet.

    The wallet balances are derived from the canonical money facts rather than
    incremented blindly:
      * every *released* revenue transaction's `seller_earning` contributes to
        `available_balance`;
      * every *held* revenue transaction's `seller_earning` makes up
        `held_balance` (escrow awaiting buyer receipt);
      * `total_earned` is the sum of all seller_earning (held + released);
      * `total_withdrawn` is the sum of *completed* withdrawal requests.
    Withdrawals debit `available` only when the admin marks them `completed`
    (the MoMo payout has actually left MUHUZE's account).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.wallets = WalletRepository(db)
        self.txns = WalletTransactionRepository(db)
        self.withdrawals = WithdrawalRequestRepository(db)
        self.revenue = RevenueTransactionRepository(db)

    # ── queries ────────────────────────────────────────────────────────────

    async def get_or_create_for_seller(self, seller_id: uuid.UUID) -> Wallet:
        wallet = await self.wallets.get_by_seller(seller_id)
        if wallet is None:
            wallet = await self.wallets.create(seller_id=seller_id)
        await self._reconcile(wallet)
        return wallet

    async def get_summary(self, seller_id: uuid.UUID) -> dict:
        wallet = await self.get_or_create_for_seller(seller_id)
        txns = await self.txns.list_for_wallet(wallet.id)
        withdrawals = await self.withdrawals.list_for_seller(seller_id)
        return {
            "wallet": wallet,
            "transactions": txns,
            "withdrawals": withdrawals,
        }

    # ── withdrawals (seller) ───────────────────────────────────────────────

    async def request_withdrawal(
        self, seller_id: uuid.UUID, *, amount: float, mobile_money_number: str, note: str | None
    ) -> WithdrawalRequest:
        wallet = await self.get_or_create_for_seller(seller_id)
        available = float(wallet.available_balance)
        if amount <= 0 or amount > available:
            raise InsufficientWalletBalanceError()
        return await self.withdrawals.create(
            wallet_id=wallet.id,
            seller_id=seller_id,
            amount=round(amount, 2),
            mobile_money_number=mobile_money_number,
            note=note,
        )

    # ── withdrawals (admin) ────────────────────────────────────────────────

    async def list_pending_withdrawals(self) -> list[WithdrawalRequest]:
        return await self.withdrawals.list_pending()

    async def update_withdrawal(
        self,
        withdrawal_id: uuid.UUID,
        *,
        status: str,
        admin_account_id: uuid.UUID | None,
        note: str | None,
    ) -> WithdrawalRequest:
        withdrawal = await self.withdrawals.get_by_id(withdrawal_id)
        if withdrawal is None:
            raise WithdrawalNotFoundError()

        target = WithdrawalStatus(status)
        current = WithdrawalStatus(withdrawal.status)

        if target == current:
            return withdrawal

        allowed = {
            WithdrawalStatus.REQUESTED: {WithdrawalStatus.PROCESSING, WithdrawalStatus.CANCELLED},
            WithdrawalStatus.PROCESSING: {WithdrawalStatus.COMPLETED, WithdrawalStatus.CANCELLED},
            WithdrawalStatus.COMPLETED: set(),
            WithdrawalStatus.CANCELLED: set(),
        }
        if target not in allowed[current]:
            raise InvalidWithdrawalStatusError()

        now = datetime.now(UTC)
        if target == WithdrawalStatus.COMPLETED:
            wallet = await self.wallets.get_by_id(withdrawal.wallet_id)
            if wallet is None:
                raise WalletNotFoundError()
            available = float(wallet.available_balance)
            if float(withdrawal.amount) > available:
                raise InsufficientWalletBalanceError()
            wallet = await self.wallets.adjust_available(
                wallet,
                delta=-float(withdrawal.amount),
                total_withdrawn_delta=float(withdrawal.amount),
            )
            await self.txns.create(
                wallet_id=wallet.id,
                type="withdrawal",
                amount=-float(withdrawal.amount),
                balance_after=float(wallet.available_balance),
                status=WalletTransactionStatus.COMPLETED,
                reference_type="WithdrawalRequest",
                reference_id=withdrawal.id,
                description=f"Withdrawal to {withdrawal.mobile_money_number} sent",
            )

        return await self.withdrawals.update_status(
            withdrawal,
            status=target.value,
            processed_by=admin_account_id,
            note=note,
            processed_at=now,
        )

    # ── admin overview ─────────────────────────────────────────────────────

    async def get_admin_overview(self) -> dict:
        wallets = await self.wallets.list_all()
        pending = await self.withdrawals.list_pending()
        available = sum(float(w.available_balance) for w in wallets)
        held = sum(float(w.held_balance) for w in wallets)
        earned = sum(float(w.total_earned) for w in wallets)
        withdrawn = sum(float(w.total_withdrawn) for w in wallets)
        return {
            "total_available": round(available, 2),
            "total_held": round(held, 2),
            "total_platform_earned": round(earned, 2),
            "total_withdrawn": round(withdrawn, 2),
            "seller_count": len(wallets),
            "withdrawals_pending": pending,
        }

    # ── reconciliation ─────────────────────────────────────────────────────

    async def _reconcile(self, wallet: Wallet) -> Wallet:
        """Rebuild the four wallet balances from revenue + withdrawals.

        Also backfills a WalletTransaction ledger row for each released
        revenue transaction (escrow released), so the seller's history shows
        the release alongside the earnings. Idempotent via the unique
        (reference_type, reference_id) guard.

        This is called on every `get_or_create_for_seller` so the wallet is
        always fresh. Balances are **computed from scratch** every time, never
        blindly incremented — the canonical money facts live in
        revenue_transactions and withdrawal_requests, not here.
        """
        # ── 1. scan revenue transactions ────────────────────────────────
        try:
            revs = await self.revenue.list_for_seller(wallet.seller_id)
            revs = list(reversed(revs))  # oldest first for chronological balance_after
        except Exception:
            revs = []

        released_earnings = 0.0
        held_earnings = 0.0
        total_earned = 0.0
        for rev in revs:
            earning = float(rev.seller_earning)
            total_earned += earning
            if rev.status == "released":
                released_earnings += earning
            else:
                held_earnings += earning

        # ── 2. scan completed withdrawals ───────────────────────────────
        withdrawals = await self.withdrawals.list_for_seller(wallet.seller_id)
        total_withdrawn = sum(
            float(w.amount) for w in withdrawals if w.status == WithdrawalStatus.COMPLETED
        )

        # ── 3. compute final balances ──────────────────────────────────
        available = max(0.0, round(released_earnings - total_withdrawn, 2))

        wallet = await self.wallets.set_balances(
            wallet,
            available=round(available, 2),
            held=round(held_earnings, 2),
            total_earned=round(total_earned, 2),
            total_withdrawn=round(total_withdrawn, 2),
        )

        # ── 4. backfill release ledger entries (idempotent) ─────────────
        # Walk released entries in creation order so balance_after shows
        # the available balance climbing after each escrow release.
        released_so_far = 0.0
        for rev in revs:
            if rev.status != "released":
                continue
            if await self.txns.exists_for_reference(
                reference_type="RevenueTransaction", reference_id=rev.id
            ):
                released_so_far += float(rev.seller_earning)
                continue
            released_so_far += float(rev.seller_earning)
            bal = round(max(0.0, released_so_far - total_withdrawn), 2)
            await self.txns.create(
                wallet_id=wallet.id,
                type="release",
                amount=float(rev.seller_earning),
                balance_after=bal,
                status=WalletTransactionStatus.COMPLETED,
                reference_type="RevenueTransaction",
                reference_id=rev.id,
                description="Earnings released after buyer receipt",
            )

        return wallet
