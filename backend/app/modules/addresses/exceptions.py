from app.shared.exceptions.base import NotFoundError


class ShippingAddressNotFoundError(NotFoundError):
    message = "Shipping address not found"
