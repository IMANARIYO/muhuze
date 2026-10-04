# Logging

**Status:** implemented (`app/core/logging.py`, `app/core/request_context_middleware.py`).

## Behavior

- One handler on the root logger, writing to stdout. Application, uvicorn, and library logs all share one format.
- Every line carries the **request id** of the request that produced it (`-` outside a request).
- One **access log line per request** (logger `app.access`): method, path, status, duration. Level: INFO for < 400, WARNING for 4xx, ERROR for 5xx. Uvicorn's own access log is disabled to avoid duplicates, and because it logs query strings.
- **Unexpected exceptions** are logged once, with stack trace and request id, by `RequestContextMiddleware` (logger `app.errors`). The client gets a generic 500.

## Configuration

| Variable | Values | Default |
|---|---|---|
| `LOG_LEVEL` | `DEBUG` `INFO` `WARNING` `ERROR` `CRITICAL` (any case) | `DEBUG` in development, `INFO` elsewhere |
| `LOG_FORMAT` | `text` `json` | `text` in development/test, `json` in staging/production |

Text (development):

```
2026-10-04 20:27:53,451 | WARNING  | app.access | [50e81433-…] | request completed | method=GET path=/nope status_code=404 duration_ms=0.67
```

JSON (staging/production, one object per line, timestamps in UTC):

```json
{"timestamp": "2026-10-04T18:28:15.008+00:00", "level": "INFO", "logger": "app.access", "request_id": "50e81433-…", "message": "request completed", "method": "GET", "path": "/nope", "status_code": 404, "duration_ms": 0.67}
```

## Writing logs

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("order created", extra={"order_id": str(order.id), "seller_count": 2})
```

- Use `extra=` for context. Don't build it into the message string. Extras become fields in JSON and `key=value` in text.
- Keep messages short, constant, and lowercase (`"order created"`), so they can be searched and grouped.
- Log important **business events** (payment confirmed, withdrawal requested) at INFO, **expected failures worth investigating** at WARNING, and **failures** at ERROR. Use `logger.exception(...)` inside `except` blocks so the stack trace is kept.
- Don't log errors that are already handled. An `AppError` raised by a service already shows up in the access log through its status code.

## Sensitive data

**Never log** passwords, tokens, secrets, private keys, payment credentials, full account numbers, identity documents, or unnecessary personal data.

As a safety net, extras whose key looks sensitive are replaced with `[REDACTED]`: any `_`/`-` word among `password`, `passwd`, `secret`, `token`, `authorization`, `cookie`, `otp`, `pin`, `cvv`, or the keys `api_key`, `apikey`, `account_number`, `card_number`, `private_key`. The redaction **does not** inspect message text, so never put sensitive values in the message itself.

Paths are logged **without query strings**, because query strings can carry tokens.
