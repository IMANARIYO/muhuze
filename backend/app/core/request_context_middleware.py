"""Request context: correlation id, access log, and the last-resort error boundary.

Written as plain ASGI middleware (not BaseHTTPMiddleware) so it wraps the
whole request — including FastAPI's exception handlers — and still sees
exceptions those handlers don't cover.
"""

import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger, request_id_var
from app.shared.responses.api_response import error_response

REQUEST_ID_HEADER = "X-Request-ID"

# Incoming ids are echoed into logs and headers, so only accept a safe shape;
# anything else is replaced to prevent log/header injection.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:\-]{1,128}$")

access_logger = get_logger("app.access")
error_logger = get_logger("app.errors")


def _resolve_request_id(scope: Scope) -> str:
    for name, value in scope.get("headers", ()):
        if name == REQUEST_ID_HEADER.lower().encode():
            candidate = value.decode("latin-1")
            if _VALID_REQUEST_ID.fullmatch(candidate):
                return candidate
            break
    return str(uuid.uuid4())


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        token = request_id_var.set(request_id)
        method, path = scope["method"], scope["path"]
        started = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                MutableHeaders(scope=message).append(REQUEST_ID_HEADER, request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            # Not swallowed: logged with its stack trace, then either turned
            # into the standard 500 envelope or, if the response already
            # started and can't be replaced, re-raised to the server.
            error_logger.exception("unhandled exception", extra={"method": method, "path": path})
            if response_started:
                raise
            response = error_response("Internal server error", 500)
            await response(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            if status_code >= 500:
                level = logging.ERROR
            elif status_code >= 400:
                level = logging.WARNING
            else:
                level = logging.INFO
            access_logger.log(
                level,
                "request completed",
                extra={
                    "method": method,
                    "path": path,  # path only: query strings can carry tokens
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)
