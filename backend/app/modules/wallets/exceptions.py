from app.shared.exceptions.base import BadRequestError, NotFoundError


class WalletNotFoundError(NotFoundError):
    message = "Wallet not found"


class InsufficientWalletBalanceError(BadRequestError):
    message = "Insufficient available wallet balance for this withdrawal"


class WithdrawalNotFoundError(NotFoundError):
    message = "Withdrawal request not found"


class InvalidWithdrawalStatusError(BadRequestError):
    message = "Invalid state transition for this withdrawal"
