"""The single response contract for every API endpoint.

Every response body, success or error, has exactly these fields:

    {"success": bool, "data": <payload or null>, "message": str, "status_code": int}

Endpoints declare `response_model=APIResponse[TheirSchema]` (for OpenAPI) and
return `success_response(...)`. The helper builds the HTTP response itself, so
the HTTP status and the body's `status_code` can never disagree.
"""

from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class APIResponse[T](BaseModel):
    success: bool = Field(description="true for 2xx responses, false for errors")
    data: T | None = Field(default=None, description="Response payload; null on errors")
    message: str = Field(description="Human-readable outcome")
    status_code: int = Field(description="Same value as the HTTP status code")


def _envelope(
    *,
    success: bool,
    data: Any,
    message: str,
    status_code: int,
    headers: dict[str, str] | None,
) -> JSONResponse:
    # mode="json" serializes nested pydantic models and encodes Decimal as a
    # string, so money never passes through float on its way to the client.
    body = APIResponse[Any](
        success=success, data=data, message=message, status_code=status_code
    ).model_dump(mode="json")
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def success_response(
    data: Any = None,
    message: str = "Request successful",
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    if not 200 <= status_code < 300 or status_code == 204:
        # 204 can't carry a body; return 200 with data=null instead.
        raise ValueError(f"success_response needs a 2xx status with a body, got {status_code}")
    return _envelope(
        success=True, data=data, message=message, status_code=status_code, headers=headers
    )


def error_response(
    message: str,
    status_code: int,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return _envelope(
        success=False, data=None, message=message, status_code=status_code, headers=headers
    )
