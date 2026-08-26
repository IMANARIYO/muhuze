from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_email(*, to: str, subject: str, body: str) -> None:
    """Sends via SMTP if configured (SMTP_HOST + friends in .env);
    otherwise logs instead of sending — same fallback this had before SMTP
    was wired up, so local dev works with zero setup.
    """
    if not settings.smtp_host:
        logger.info(
            "EMAIL (no SMTP configured, logging only) to=%s subject=%r body=%r",
            to,
            subject,
            body,
        )
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from_email or settings.smtp_username
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        start_tls=settings.smtp_use_tls,
    )
