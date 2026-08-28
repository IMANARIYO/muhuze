from app.shared.exceptions.base import BadRequestError, NotFoundError


class OrderNotFoundError(NotFoundError):
    message = "Order not found"


class EmptyCartError(BadRequestError):
    message = "Your cart is empty — add items before checking out"


class ShippingDestinationRequiredError(BadRequestError):
    message = "A shipping destination is required (choose a saved address or provide one)"


class CartItemUnavailableError(BadRequestError):
    message = "One or more items in your cart are no longer available"


class InsufficientStockError(BadRequestError):
    message = "Not enough stock for an item in your cart"


class SellerOrderNotFoundError(NotFoundError):
    message = "Seller order not found"


class ShipmentNotFoundError(NotFoundError):
    message = "Shipment not found"


class SellerOrderStateError(BadRequestError):
    message = "Invalid fulfillment state transition"
