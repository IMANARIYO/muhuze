from enum import StrEnum


class WalletTransactionKind(StrEnum):
    """Why a wallet's balances moved."""

    EARNING = "earning"  # a paid sale: + pending
    SETTLEMENT = "settlement"  # the buyer confirmed receipt: pending → available
    REVERSAL = "reversal"  # a paid sale was undone: − pending
    WITHDRAWAL = "withdrawal"  # a withdrawal was requested: − available (reserved)
    WITHDRAWAL_RELEASE = "withdrawal_release"  # rejected, failed, or cancelled: + available
    WITHDRAWAL_COMPLETE = (
        "withdrawal_complete"  # paid out: total_withdrawn + amount, balances unchanged
    )


DEFAULT_CURRENCY = "RWF"
