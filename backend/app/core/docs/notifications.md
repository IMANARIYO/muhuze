# Email (`app/core/notifications.py`)

## What it is

`send_email(*, to, subject, body)` — the one function every module calls
to send an email (currently: `auth`'s OTP verification and password-reset
flows). Sends via SMTP when configured; **falls back to logging instead of
sending when it isn't** — this is what let the rest of the app be built
and tested before any real provider was chosen.

## Configuration

`.env`: `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USERNAME`,
`SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` (default `true`).

- **`SMTP_HOST` unset** → logs `EMAIL (no SMTP configured, logging only) ...` instead of sending. This is the current state of the checked-in `.env` — real credentials haven't been supplied.
- **`SMTP_HOST` set** → sends for real via `aiosmtplib`.
- **`SMTP_FROM_EMAIL` unset but `SMTP_USERNAME` set** → falls back to using the username as the From address (the common case for a plain mailbox-as-relay setup, e.g. Gmail SMTP).

Works with any SMTP-speaking provider or mailbox — Gmail SMTP (with an app
password), a hosting provider's SMTP, Mailtrap for testing, a dedicated
transactional-email SMTP endpoint (SendGrid/Mailgun/SES all expose one)
— nothing provider-specific is hardcoded.

## Why async

`send_email` is `async def` because real SMTP sending (`aiosmtplib.send`)
is a network call. Every call site must `await` it — see `AuthService`'s
two call sites for the pattern.

## Testing

Tests never hit a real SMTP server. `tests/conftest.py::captured_emails`
monkeypatches `send_email` itself (an async fake) for auth-flow tests that
just need to capture what *would* have been sent — see
`tests/test_verification.py`, `test_password_reset.py`. `tests/test_notifications.py`
tests `send_email` directly, monkeypatching `aiosmtplib.send` one level
deeper to verify the log-fallback and the real-send path.
