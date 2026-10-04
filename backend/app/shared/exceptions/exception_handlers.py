"""Global handlers that map expected exceptions onto the standard error envelope.

Unexpected exceptions are deliberately NOT handled here: they propagate to
RequestContextMiddleware (app/core/request_context_middleware.py), which logs them with the
request id still in context and returns a generic 500 envelope.
"""

from collections.abc import Sequence
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.exceptions.application_exceptions import AppError
from app.shared.responses.api_response import error_response

# First element of a validation error's `loc` names where the value came from.
_REQUEST_SOURCES = {"body", "query", "path", "header", "cookie"}


def format_validation_errors(errors: Sequence[Any]) -> str:
    """One readable message listing every invalid field.

    Only the field location and pydantic's message are used — never the
    submitted `input`, which could be a password or token.
    """
    parts = []
    for error in errors:
        loc = [str(part) for part in error.get("loc", ())]
        if loc and loc[0] in _REQUEST_SOURCES:
            loc = loc[1:]
        field = ".".join(loc)
        parts.append(f"{field}: {error['msg']}" if field else error["msg"])
    return "; ".join(parts) or "Invalid request"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.message, exc.status_code)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
    # Keep headers such as Allow (405) and WWW-Authenticate (401).
    return error_response(message, exc.status_code, headers=exc.headers)


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        format_validation_errors(exc.errors()), status.HTTP_422_UNPROCESSABLE_CONTENT
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
