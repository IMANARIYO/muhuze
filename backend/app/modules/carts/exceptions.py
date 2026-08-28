from app.shared.exceptions.base import NotFoundError


class CartItemNotFoundError(NotFoundError):
    message = "Cart item not found"
