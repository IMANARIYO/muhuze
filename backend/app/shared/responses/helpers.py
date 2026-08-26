from app.shared.responses.schemas import APIResponse


def success_response[T](data: T | None = None, message: str = "Success") -> APIResponse[T]:
    return APIResponse(status="success", message=message, data=data)


def error_response(message: str, data: None = None) -> APIResponse[None]:
    return APIResponse(status="error", message=message, data=data)
