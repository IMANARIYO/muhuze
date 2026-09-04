import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wallets.models import (
    Wallet,
    WalletTransaction,
    WithdrawalRequest,
)


class WalletRepository:
    """Data access for wallets. No business rules here — those live in
    WalletService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_seller(self, seller_id: uuid.UUID) -> Wallet | None:
        result = await self.db.execute(
            select(Wallet).where(Wallet.seller_id == seller_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, wallet_id: uuid.UUID) -> Wallet | None:
        result = await self.db.execute(
            select(Wallet).where(Wallet.id == wallet_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, *, seller_id: uuid.UUID, currency: str = "RWF"
    ) -> Wallet:
        wallet = Wallet(seller_id=seller_id, currency=currency)
        self.db.add(wallet)
        await self.db.flush()
        await self.db.refresh(wallet)
        return wallet

    async def list_all(self) -> list[Wallet]:
        result = await self.db.execute(
            select(Wallet).order_by(Wallet.created_at.asc())
        )
        return list(result.scalars().all())

    async def set_balances(
        self,
        wallet: Wallet,
        *,
        available: float,
        held: float,
        total_earned: float,
        total_withdrawn: float,
    ) -> Wallet:
        wallet.available_balance = available
        wallet.held_balance = held
        wallet.total_earned = total_earned
        wallet.total_withdrawn = total_withdrawn
        await self.db.flush()
        await self.db.refresh(wallet)
        return wallet

    async def adjust_available(
        self, wallet: Wallet, *, delta: float, total_withdrawn_delta: float = 0.0
    ) -> Wallet:
        return await self.set_balances(
            wallet,
            available=max(0.0, round(float(wallet.available_balance) + delta, 2)),
            held=float(wallet.held_balance),
            total_earned=float(wallet.total_earned),
            total_withdrawn=round(
                float(wallet.total_withdrawn) + total_withdrawn_delta, 2
            ),
        )


class WalletTransactionRepository:
    """Data access for the wallet ledger."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_wallet(self, wallet_id: uuid.UUID) -> list[WalletTransaction]:
        result = await self.db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[WalletTransaction]:
        result = await self.db.execute(
            select(WalletTransaction).order_by(WalletTransaction.created_at.desc())
        )
        return list(result.scalars().all())

    async def exists_for_reference(
        self, *, reference_type: str, reference_id: uuid.UUID
    ) -> bool:
        result = await self.db.execute(
            select(WalletTransaction.id).where(
                WalletTransaction.reference_type == reference_type,
                WalletTransaction.reference_id == reference_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        wallet_id: uuid.UUID,
        type: str,
        amount: float,
        balance_after: float,
        currency: str = "RWF",
        status: str = "completed",
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
        description: str | None = None,
    ) -> WalletTransaction:
        txn = WalletTransaction(
            wallet_id=wallet_id,
            type=type,
            amount=amount,
            balance_after=balance_after,
            currency=currency,
            status=status,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn


class WithdrawalRequestRepository:
    """Data access for withdrawal requests."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, withdrawal_id: uuid.UUID) -> WithdrawalRequest | None:
        result = await self.db.execute(
            select(WithdrawalRequest).where(WithdrawalRequest.id == withdrawal_id)
        )
        return result.scalar_one_or_none()

    async def list_for_seller(self, seller_id: uuid.UUID) -> list[WithdrawalRequest]:
        result = await self.db.execute(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.seller_id == seller_id)
            .order_by(WithdrawalRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_pending(self) -> list[WithdrawalRequest]:
        result = await self.db.execute(
            select(WithdrawalRequest)
            .where(
                WithdrawalRequest.status.in_(["requested", "processing"])
            )
            .order_by(WithdrawalRequest.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        wallet_id: uuid.UUID,
        seller_id: uuid.UUID,
        amount: float,
        mobile_money_number: str,
        currency: str = "RWF",
        note: str | None = None,
    ) -> WithdrawalRequest:
        wd = WithdrawalRequest(
            wallet_id=wallet_id,
            seller_id=seller_id,
            amount=amount,
            currency=currency,
            mobile_money_number=mobile_money_number,
            note=note,
        )
        self.db.add(wd)
        await self.db.flush()
        await self.db.refresh(wd)
        return wd

    async def update_status(
        self,
        withdrawal: WithdrawalRequest,
        *,
        status: str,
        processed_by: uuid.UUID | None = None,
        note: str | None = None,
        processed_at=None,
    ) -> WithdrawalRequest:
        withdrawal.status = status
        if processed_by is not None:
            withdrawal.processed_by = processed_by
        if note is not None:
            withdrawal.note = note
        if processed_at is not None:
            withdrawal.processed_at = processed_at
        await self.db.flush()
        await self.db.refresh(withdrawal)
        return withdrawal
