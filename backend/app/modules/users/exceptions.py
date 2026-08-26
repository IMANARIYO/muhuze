from app.shared.exceptions.base import NotFoundError


class ProfileNotFoundError(NotFoundError):
    message = "Profile not found"
