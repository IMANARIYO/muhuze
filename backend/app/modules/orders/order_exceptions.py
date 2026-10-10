from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)


class OrderNotFoundError(NotFoundError):
    message = "Order not found"


class ProductsUnavailableError(BusinessRuleError):
    message = "Some products are no longer available"


class OwnProductOrderError(BusinessRuleError):
    message = "You cannot order products from your own shop"


class MixedCurrencyOrderError(BusinessRuleError):
    message = "All products in one order must be priced in the same currency"


class OrderStatusConflictError(ConflictError):
    message = "This action is not allowed in the order's current status"
