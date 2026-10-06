from enum import StrEnum


class WalletTransactionKind(StrEnum):
    """Why a wallet's balances moved. More kinds (withdrawal, …) join with
    the features that need them."""

    EARNING = "earning"  # a paid sale: + pending
    SETTLEMENT = "settlement"  # the buyer confirmed receipt: pending → available
    REVERSAL = "reversal"  # a paid sale was undone: − pending


DEFAULT_CURRENCY = "RWF"
