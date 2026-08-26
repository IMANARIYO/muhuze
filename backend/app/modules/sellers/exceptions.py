from app.shared.exceptions.base import ConflictError, NotFoundError


class SellerNotFoundError(NotFoundError):
    message = "Seller not found"


class StoreNameAlreadyTakenError(ConflictError):
    message = "This store name is already taken"
