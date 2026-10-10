"""Application-wide logging configuration.

- One stdout handler on the root logger, so app, uvicorn, and library logs
  share a single format.
- `text` format for local development, `json` (one object per line) for
  staging/production log collectors. See Settings.effective_log_format.
- Every line carries the current request id (set by RequestContextMiddleware).
- Structured context goes in `extra=`; it is rendered as fields, and values
  under sensitive-looking keys (password, token, secret, …) are redacted.

    logger = get_logger(__name__)
    logger.info("order created", extra={"order_id": str(order.id)})
"""

import contextvars
import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

from app.config.settings import Settings

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

REDACTED = "[REDACTED]"

# A key is sensitive if any of its `_`/`-`-separated words is in this set, or
# if the whole key is listed below. Word matching (not substring matching)
# keeps "shipping_fee" from being redacted because it contains "pin".
_SENSITIVE_WORDS = frozenset(
    {"password", "passwd", "secret", "token", "authorization", "cookie", "otp", "pin", "cvv"}
)
_SENSITIVE_KEYS = frozenset({"api_key", "apikey", "account_number", "card_number", "private_key"})

# Attributes every LogRecord has; anything else on a record came from `extra=`.
# `color_message` is uvicorn's ANSI-colored duplicate of the message.
_STANDARD_RECORD_ATTRS = frozenset(
    vars(logging.LogRecord("", logging.INFO, "", 0, "", None, None))
) | {"message", "asctime", "request_id", "color_message"}

TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | [%(request_id)s] | %(message)s"

_HANDLER_MARKER = "_muhuze_handler"

# Loggers that are too chatty at DEBUG to be useful.
_QUIET_LOGGERS = ("asyncio", "httpx", "httpcore", "multipart", "python_multipart", "watchfiles")


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return lowered in _SENSITIVE_KEYS or any(
        word in _SENSITIVE_WORDS for word in re.split(r"[_\-]", lowered)
    )


def extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in vars(record).items()
        if key not in _STANDARD_RECORD_ATTRS and not key.startswith("_")
    }


class RequestContextFilter(logging.Filter):
    """Stamps the request id on every record and redacts sensitive extras."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        for key in extra_fields(record):
            if is_sensitive_key(key):
                setattr(record, key, REDACTED)
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        # Extras come after the standard fields and can never overwrite them.
        for key, value in extra_fields(record).items():
            payload.setdefault(key, value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(TEXT_FORMAT)

    def formatMessage(self, record: logging.LogRecord) -> str:
        line = super().formatMessage(record)
        extras = extra_fields(record)
        if extras:
            line += " | " + " ".join(f"{key}={value}" for key, value in extras.items())
        return line


def configure_logging(settings: Settings) -> None:
    """Install the app's handler on the root logger. Safe to call repeatedly.

    Only handlers installed by this function are replaced, so handlers added
    by others (e.g. pytest's log capture) are left alone.
    """
    handler = logging.StreamHandler(sys.stdout)
    setattr(handler, _HANDLER_MARKER, True)
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(
        JSONFormatter() if settings.effective_log_format == "json" else TextFormatter()
    )

    root = logging.getLogger()
    for existing in [h for h in root.handlers if getattr(h, _HANDLER_MARKER, False)]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(settings.effective_log_level)

    # Route uvicorn's server logs through the root handler (one format).
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    # Replaced by RequestContextMiddleware's access log, which adds the
    # request id and duration and never logs query strings.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.disabled = True

    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
