"""Email delivery behind one small interface.

Business code depends on `EmailSender` only and never imports an email
library. `build_email_sender` picks the adapter from settings: SMTP when
`SMTP_HOST` is configured, otherwise a logging stand-in that is only allowed
outside staging and production (enforced by `Settings`).
"""

from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.config.settings import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SMTP_TIMEOUT_SECONDS = 10


class EmailDeliveryError(Exception):
    """The email could not be handed to the mail server."""


class EmailSender(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None:
        """Deliver a plain-text email, or raise EmailDeliveryError."""


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(self, *, to: str, subject: str, body: str) -> None:
        settings = self._settings
        message = EmailMessage()
        message["From"] = settings.email_from_address
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        password = settings.smtp_password
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=password.get_secret_value() if password else None,
                start_tls=settings.smtp_use_tls,
                timeout=SMTP_TIMEOUT_SECONDS,
            )
        except (aiosmtplib.SMTPException, OSError) as exc:
            raise EmailDeliveryError(f"SMTP delivery failed: {type(exc).__name__}") from exc


class LoggingEmailSender:
    """Development and test stand-in: writes the email to the log.

    The body is logged on purpose. It is the only way to read a verification
    code or reset link on a machine with no mail server, and `Settings`
    refuses to start staging/production without SMTP, so this adapter never
    runs there.
    """

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info(
            "email not sent: SMTP is not configured",
            extra={"to": to, "subject": subject, "body": body},
        )


def build_email_sender(settings: Settings) -> EmailSender:
    if settings.smtp_host is None:
        return LoggingEmailSender()
    return SmtpEmailSender(settings)
