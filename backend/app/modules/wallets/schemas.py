import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Wallet ID")
    seller_id: uuid.UUID = Field(description="Owning seller")
    available_balance: float = Field(description="Balance ready to withdraw")
    held_balance: float = Field(description="Escrow awaiting buyer receipt")
    total_earned: float = Field(description="Lifetime net earnings (net of commission)")
    total_withdrawn: float = Field(description="Lifetime money sent out via withdrawals")
    currency: str = Field(description="Billing currency")
    created_at: datetime = Field(description="When the wallet was created")


class WalletTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Ledger entry ID")
    wallet_id: uuid.UUID = Field(description="Owning wallet")
    type: str = Field(description="earnings | release | withdrawal | adjustment")
    amount: float = Field(description="Signed movement (positive = credit)")
    balance_after: float = Field(description="Available balance after this entry")
    currency: str = Field(description="Currency")
    status: str = Field(description="pending | completed | failed | cancelled")
    reference_type: str | None = Field(description="Source entity type, if any")
    reference_id: uuid.UUID | None = Field(description="Source entity id, if any")
    description: str | None = Field(description="Human description")
    created_at: datetime = Field(description="When recorded")


class CreateWithdrawalRequest(BaseModel):
    """A seller asks to withdraw available_balance to their own MoMo number."""

    amount: float = Field(gt=0, description="Amount to withdraw (must be <= available balance)")
    mobile_money_number: str = Field(
        min_length=1, max_length=20, description="Your mobile-money number for the payout"
    )
    note: str | None = Field(default=None, max_length=255, description="Optional note")


class WithdrawalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Withdrawal request ID")
    wallet_id: uuid.UUID = Field(description="Owning wallet")
    seller_id: uuid.UUID = Field(description="Requesting seller")
    amount: float = Field(description="Amount requested")
    currency: str = Field(description="Currency")
    mobile_money_number: str = Field(description="Payout mobile-money number")
    status: str = Field(description="requested | processing | completed | cancelled")
    note: str | None = Field(description="Note")
    processed_by: uuid.UUID | None = Field(description="Admin account that resolved it")
    processed_at: datetime | None = Field(description="When resolved")
    created_at: datetime = Field(description="When requested")


class WalletSummaryResponse(BaseModel):
    """A seller's wallet plus recent ledger entries."""

    wallet: WalletResponse = Field(description="Current balances")
    transactions: list[WalletTransactionResponse] = Field(
        default_factory=list, description="Ledger history (newest first)"
    )
    withdrawals: list[WithdrawalResponse] = Field(
        default_factory=list, description="Withdrawal requests (newest first)"
    )


class AdminWalletOverviewResponse(BaseModel):
    """Platform-wide wallet picture for an admin."""

    total_available: float = Field(description="Sum of all sellers' available balances")
    total_held: float = Field(description="Sum of all sellers' held (escrow) balances")
    total_platform_earned: float = Field(description="Sum of all sellers' total_earned")
    total_withdrawn: float = Field(description="Sum of all money paid out")
    seller_count: int = Field(description="Number of wallets tracked")
    withdrawals_pending: list[WithdrawalResponse] = Field(
        default_factory=list, description="Withdrawals awaiting admin action"
    )


class UpdateWithdrawalRequest(BaseModel):
    """Admin-driven state change on a withdrawal request."""

    status: str = Field(
        description="processing | completed | cancelled",
        pattern="^(processing|completed|cancelled)$",
    )
    note: str | None = Field(default=None, max_length=255, description="Admin note")
