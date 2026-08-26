from app.core.logging import get_logger

logger = get_logger(__name__)


def send_email(*, to: str, subject: str, body: str) -> None:
    """Stub: logs instead of actually sending. Swap this for a real provider
    (SES/SendGrid/etc.) before production — everything that calls this
    (OTP codes, password reset links) is otherwise complete. See
    app/modules/auth/docs/roadmap.md.
    """
    logger.info("EMAIL to=%s subject=%r body=%r", to, subject, body)
