from app.shared.exceptions.base import ConflictError


class RevenueAlreadyRecordedError(ConflictError):
    message = "Revenue for this order/seller has already been recorded"
