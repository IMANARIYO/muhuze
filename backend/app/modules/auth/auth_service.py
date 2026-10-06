"""Authentication business rules: accounts, sessions, email verification,
and password recovery. Rules are documented in docs/features/001_authentication.md.

Every public method is one unit of work and commits it itself. Some commit
*before* raising on purpose (a wrong verification code still costs an attempt;
a reused refresh token still revokes the account's sessions).
"""

import hmac
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.core.clock import utc_now
from app.core.logging import get_logger
from app.core.security import (
    InvalidAccessTokenError,
    PasswordHasher,
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    generate_otp,
    hash_token,
)
from app.infrastructure.notifications.email_sender import EmailDeliveryError, EmailSender
from app.modules.auth.auth_constants import AccountStatus, VerificationPurpose
from app.modules.auth.auth_exceptions import (
    AccountNotActiveError,
    EmailAlreadyRegisteredError,
    EmailNotVerifiedError,
    IncorrectCurrentPasswordError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
    InvalidVerificationCodeError,
    PhoneAlreadyRegisteredError,
    SessionNotFoundError,
)
from app.modules.auth.auth_model import (
    Account,
    PasswordResetToken,
    RefreshToken,
    VerificationCode,
)
from app.modules.auth.auth_repository import (
    AccountRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    VerificationCodeRepository,
)
from app.modules.auth.auth_schema import SessionResponse
from app.shared.exceptions.application_exceptions import AuthenticationError
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

PHONE_UNIQUE_CONSTRAINT = "uq_accounts_phone"


@dataclass(frozen=True, slots=True)
class ClientInfo:
    """Where a session was opened from, shown to the owner in the session list."""

    user_agent: str | None
    ip_address: str | None


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class AuthenticatedAccount:
    account: Account
    session_id: uuid.UUID


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        password_hasher: PasswordHasher,
        email_sender: EmailSender,
    ) -> None:
        self._session = session
        self._settings = settings
        self._password_hasher = password_hasher
        self._email_sender = email_sender
        self._accounts = AccountRepository(session)
        self._refresh_tokens = RefreshTokenRepository(session)
        self._verification_codes = VerificationCodeRepository(session)
        self._password_reset_tokens = PasswordResetTokenRepository(session)

    # ── Registration and email verification ──────────────────────────────

    async def register(
        self, *, email: str, password: str, full_name: str, phone: str | None
    ) -> Account:
        email = _normalize_email(email)
        if await self._accounts.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()
        if phone is not None and await self._accounts.get_by_phone(phone) is not None:
            raise PhoneAlreadyRegisteredError()

        account = Account(
            email=email,
            phone=phone,
            password_hash=await self._password_hasher.hash(password),
            full_name=full_name,
        )
        try:
            await self._accounts.add(account)
        except IntegrityError as exc:
            # Lost a race with a concurrent registration for the same email/phone.
            await self._session.rollback()
            if PHONE_UNIQUE_CONSTRAINT in str(exc.orig):
                raise PhoneAlreadyRegisteredError() from exc
            raise EmailAlreadyRegisteredError() from exc

        code = await self._issue_verification_code(account)
        await self._session.commit()
        logger.info("account registered", extra={"account_id": str(account.id)})

        await self._send_verification_email(account, code)
        return account

    async def request_email_verification(self, *, email: str) -> None:
        """Send a fresh code. Silent when there is nothing to verify, so the
        endpoint never reveals whether an email is registered."""
        account = await self._accounts.get_by_email(_normalize_email(email))
        if account is None or account.is_verified or account.status != AccountStatus.ACTIVE:
            return
        code = await self._issue_verification_code(account)
        await self._session.commit()
        await self._send_verification_email(account, code)

    async def confirm_email_verification(self, *, email: str, code: str) -> None:
        account = await self._accounts.get_by_email(_normalize_email(email))
        if account is None or account.is_verified:
            raise InvalidVerificationCodeError()

        now = utc_now()
        stored = await self._verification_codes.get_unused_for_update(
            account_id=account.id, purpose=VerificationPurpose.EMAIL_VERIFICATION.value, now=now
        )
        if stored is None or stored.attempts >= self._settings.verification_code_max_attempts:
            raise InvalidVerificationCodeError()

        if not hmac.compare_digest(stored.code_hash, hash_token(code)):
            stored.attempts += 1
            await self._session.commit()
            logger.warning(
                "email verification failed",
                extra={"account_id": str(account.id), "attempts": stored.attempts},
            )
            raise InvalidVerificationCodeError()

        stored.used_at = now
        account.is_verified = True
        account.verified_at = now
        await self._session.commit()
        logger.info("email verified", extra={"account_id": str(account.id)})

    # ── Sessions ─────────────────────────────────────────────────────────

    async def login(self, *, email: str, password: str, client: ClientInfo) -> TokenPair:
        account = await self._accounts.get_by_email(_normalize_email(email))
        if account is None:
            await self._password_hasher.verify_dummy(password)
            raise InvalidCredentialsError()
        if not await self._password_hasher.verify(password, account.password_hash):
            logger.warning("login failed", extra={"account_id": str(account.id)})
            raise InvalidCredentialsError()
        if account.status != AccountStatus.ACTIVE:
            raise AccountNotActiveError()
        if not account.is_verified:
            raise EmailNotVerifiedError()

        now = utc_now()
        account.last_login_at = now
        tokens = await self._open_session(account.id, client, now)
        await self._session.commit()
        logger.info("login succeeded", extra={"account_id": str(account.id)})
        return tokens

    async def refresh(self, *, refresh_token: str, client: ClientInfo) -> TokenPair:
        """Exchange a refresh token for a new pair. The presented token is
        revoked (rotation), so each refresh token works exactly once."""
        stored = await self._refresh_tokens.get_by_token_hash_for_update(hash_token(refresh_token))
        if stored is None:
            raise InvalidRefreshTokenError()

        now = utc_now()
        if stored.rotated_at is not None:
            # This token was already exchanged once. Either the owner or a
            # thief is now holding a stale copy, and we can't tell which, so
            # every session of the account ends.
            revoked = await self._refresh_tokens.revoke_all(account_id=stored.account_id, now=now)
            await self._session.commit()
            logger.warning(
                "refresh token reuse detected",
                extra={"account_id": str(stored.account_id), "sessions_revoked": revoked},
            )
            raise InvalidRefreshTokenError()
        if stored.revoked_at is not None or stored.expires_at <= now:
            raise InvalidRefreshTokenError()

        stored.revoked_at = now
        account = await self._accounts.get_by_id(stored.account_id)
        if account is None or account.status != AccountStatus.ACTIVE:
            await self._session.commit()
            raise InvalidRefreshTokenError()

        stored.rotated_at = now
        tokens = await self._open_session(account.id, client, now)
        await self._session.commit()
        return tokens

    async def logout(self, *, refresh_token: str) -> None:
        """End one session. Succeeds even if the token is unknown or already revoked."""
        stored = await self._refresh_tokens.get_by_token_hash_for_update(hash_token(refresh_token))
        if stored is None or stored.revoked_at is not None:
            return
        stored.revoked_at = utc_now()
        await self._session.commit()
        logger.info("logout", extra={"account_id": str(stored.account_id)})

    async def logout_all(self, *, account_id: uuid.UUID) -> None:
        revoked = await self._refresh_tokens.revoke_all(account_id=account_id, now=utc_now())
        await self._session.commit()
        logger.info(
            "all sessions revoked",
            extra={"account_id": str(account_id), "sessions_revoked": revoked},
        )

    async def authenticate(self, access_token: str) -> AuthenticatedAccount:
        """Resolve an access token to its account. Every failure is the same
        401, so a caller can't tell a bad token from a blocked account."""
        try:
            claims = decode_access_token(self._settings, access_token)
        except InvalidAccessTokenError as exc:
            raise AuthenticationError() from exc
        account = await self._accounts.get_by_id(claims.account_id)
        if account is None or account.status != AccountStatus.ACTIVE:
            raise AuthenticationError()
        return AuthenticatedAccount(account=account, session_id=claims.session_id)

    async def list_sessions(
        self, *, auth: AuthenticatedAccount, pagination: PaginationParams
    ) -> Page[SessionResponse]:
        now = utc_now()
        account_id = auth.account.id
        sessions = await self._refresh_tokens.list_active(
            account_id=account_id, now=now, offset=pagination.offset, limit=pagination.limit
        )
        total = await self._refresh_tokens.count_active(account_id=account_id, now=now)
        items = [
            SessionResponse(
                id=session.id,
                user_agent=session.user_agent,
                ip_address=session.ip_address,
                created_at=session.created_at,
                expires_at=session.expires_at,
                is_current=session.id == auth.session_id,
            )
            for session in sessions
        ]
        return Page[SessionResponse].build(items, total, pagination)

    async def revoke_session(self, *, account_id: uuid.UUID, session_id: uuid.UUID) -> None:
        """End one of the caller's own sessions. Someone else's session looks
        exactly like one that doesn't exist."""
        now = utc_now()
        session = await self._refresh_tokens.get_active(
            session_id=session_id, account_id=account_id, now=now
        )
        if session is None:
            raise SessionNotFoundError()
        session.revoked_at = now
        await self._session.commit()
        logger.info("session revoked", extra={"account_id": str(account_id)})

    # ── Passwords ────────────────────────────────────────────────────────

    async def change_password(
        self, *, auth: AuthenticatedAccount, current_password: str, new_password: str
    ) -> None:
        """Change the password and sign out every other device."""
        account = auth.account
        if not await self._password_hasher.verify(current_password, account.password_hash):
            raise IncorrectCurrentPasswordError()
        account.password_hash = await self._password_hasher.hash(new_password)
        await self._refresh_tokens.revoke_all(
            account_id=account.id, now=utc_now(), except_id=auth.session_id
        )
        await self._session.commit()
        logger.info("password changed", extra={"account_id": str(account.id)})

    async def request_password_reset(self, *, email: str) -> None:
        """Email a single-use reset link. Silent for unknown or inactive
        accounts, so the endpoint never reveals whether an email is registered."""
        account = await self._accounts.get_by_email(_normalize_email(email))
        if account is None or account.status != AccountStatus.ACTIVE:
            return

        raw_token = generate_opaque_token()
        lifetime = self._settings.password_reset_token_expire_minutes
        # Only the newest link works.
        await self._password_reset_tokens.delete_unused(account_id=account.id)
        await self._password_reset_tokens.add(
            PasswordResetToken(
                account_id=account.id,
                token_hash=hash_token(raw_token),
                expires_at=utc_now() + timedelta(minutes=lifetime),
            )
        )
        await self._session.commit()
        logger.info("password reset requested", extra={"account_id": str(account.id)})

        await self._send_email(
            account,
            subject="Reset your MUHUZE password",
            body=(
                "Use this link to choose a new password:\n\n"
                f"{self._settings.password_reset_url}?token={raw_token}\n\n"
                f"The link expires in {lifetime} minutes and can be used once. "
                "If you didn't ask for it, you can ignore this email."
            ),
        )

    async def reset_password(self, *, token: str, new_password: str) -> None:
        stored = await self._password_reset_tokens.get_by_token_hash_for_update(hash_token(token))
        now = utc_now()
        if stored is None or stored.used_at is not None or stored.expires_at <= now:
            raise InvalidPasswordResetTokenError()
        account = await self._accounts.get_by_id(stored.account_id)
        if account is None:
            raise InvalidPasswordResetTokenError()

        account.password_hash = await self._password_hasher.hash(new_password)
        stored.used_at = now
        # Whoever knew the old password must not keep a session.
        await self._refresh_tokens.revoke_all(account_id=account.id, now=now)
        await self._session.commit()
        logger.info("password reset completed", extra={"account_id": str(account.id)})

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _open_session(
        self, account_id: uuid.UUID, client: ClientInfo, now: datetime
    ) -> TokenPair:
        raw_refresh_token = generate_opaque_token()
        session_id = uuid.uuid4()
        await self._refresh_tokens.add(
            RefreshToken(
                id=session_id,
                account_id=account_id,
                token_hash=hash_token(raw_refresh_token),
                expires_at=now + timedelta(days=self._settings.refresh_token_expire_days),
                user_agent=client.user_agent,
                ip_address=client.ip_address,
            )
        )
        return TokenPair(
            access_token=create_access_token(
                self._settings, account_id=account_id, session_id=session_id
            ),
            refresh_token=raw_refresh_token,
            expires_in=self._settings.access_token_expire_minutes * 60,
        )

    async def _issue_verification_code(self, account: Account) -> str:
        """Replace the account's pending email code with a new one. Not committed here."""
        purpose = VerificationPurpose.EMAIL_VERIFICATION.value
        code = generate_otp()
        await self._verification_codes.delete_unused(account_id=account.id, purpose=purpose)
        await self._verification_codes.add(
            VerificationCode(
                account_id=account.id,
                purpose=purpose,
                code_hash=hash_token(code),
                expires_at=utc_now()
                + timedelta(minutes=self._settings.verification_code_expire_minutes),
            )
        )
        return code

    async def _send_verification_email(self, account: Account, code: str) -> None:
        await self._send_email(
            account,
            subject="Your MUHUZE verification code",
            body=(
                f"Your verification code is {code}.\n\n"
                f"It expires in {self._settings.verification_code_expire_minutes} minutes. "
                "If you didn't create a MUHUZE account, you can ignore this email."
            ),
        )

    async def _send_email(self, account: Account, *, subject: str, body: str) -> None:
        """Send after the commit. A delivery failure is logged, not raised:
        the code or link is already stored and can be requested again, and an
        error here would reveal that the email belongs to an account."""
        try:
            await self._email_sender.send(to=account.email, subject=subject, body=body)
        except EmailDeliveryError:
            logger.exception("email delivery failed", extra={"account_id": str(account.id)})


def _normalize_email(email: str) -> str:
    return email.strip().lower()
