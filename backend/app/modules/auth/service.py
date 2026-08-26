import uuid
from datetime import UTC, datetime, timedelta

from app.core import notifications
from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_otp,
    generate_password_reset_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.exceptions import (
    AccountNotFoundError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidRefreshTokenError,
    InvalidVerificationCodeError,
    PermissionNotFoundError,
    RoleNotFoundError,
)
from app.modules.auth.models import Account, Permission, Role, VerificationPurpose
from app.modules.auth.repository import (
    AccountRepository,
    AuthorizationRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    VerificationCodeRepository,
)


class AuthService:
    """Business rules for registration, login, and session refresh."""

    def __init__(
        self,
        accounts: AccountRepository,
        refresh_tokens: RefreshTokenRepository,
        authorization: AuthorizationRepository,
    ) -> None:
        self.accounts = accounts
        self.refresh_tokens = refresh_tokens
        self.authorization = authorization

    async def register(
        self, *, email: str, phone: str | None, password: str
    ) -> Account:
        if await self.accounts.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError()
        account = await self.accounts.create(
            email=email,
            phone=phone,
            password_hash=hash_password(password),
        )
        # Every account starts as a buyer. Becoming a seller is a separate,
        # later action (assigns the "seller" role when that module is wired
        # up) — this only grants the default.
        buyer_role = await self.authorization.get_role_by_name("buyer")
        if buyer_role is not None:
            await self.authorization.assign_role(
                account_id=account.id, role_id=buyer_role.id
            )
        return account

    async def login(self, *, email: str, password: str) -> tuple[str, str]:
        account = await self.accounts.get_by_email(email)
        if account is None or not verify_password(password, account.password_hash):
            raise InvalidCredentialsError()
        if not account.is_active:
            raise InvalidCredentialsError()
        access_token = create_access_token(subject=str(account.id))
        refresh_token = await self._issue_refresh_token(account.id)
        return access_token, refresh_token

    async def refresh(self, *, raw_refresh_token: str) -> tuple[str, str]:
        """Rotates the refresh token: the old one is revoked and a new one is
        issued alongside the new access token, so a stolen-and-reused refresh
        token is detectable (it will already be revoked)."""
        stored = await self.refresh_tokens.get_by_token_hash(
            hash_token(raw_refresh_token)
        )
        is_expired = stored is not None and stored.expires_at < datetime.now(UTC)
        if stored is None or stored.revoked_at is not None or is_expired:
            raise InvalidRefreshTokenError()

        await self.refresh_tokens.revoke(stored)
        access_token = create_access_token(subject=str(stored.account_id))
        new_refresh_token = await self._issue_refresh_token(stored.account_id)
        return access_token, new_refresh_token

    async def logout(self, *, raw_refresh_token: str) -> None:
        stored = await self.refresh_tokens.get_by_token_hash(
            hash_token(raw_refresh_token)
        )
        if stored is not None and stored.revoked_at is None:
            await self.refresh_tokens.revoke(stored)

    async def _issue_refresh_token(self, account_id: uuid.UUID) -> str:
        raw_token = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        await self.refresh_tokens.create(
            account_id=account_id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        return raw_token


class VerificationService:
    """Business rules for email verification via one-time codes."""

    def __init__(
        self,
        accounts: AccountRepository,
        verification_codes: VerificationCodeRepository,
    ) -> None:
        self.accounts = accounts
        self.verification_codes = verification_codes

    async def request_email_verification(self, account: Account) -> None:
        code = generate_otp()
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.otp_expire_minutes)
        await self.verification_codes.create(
            account_id=account.id,
            purpose=VerificationPurpose.EMAIL_VERIFICATION,
            code_hash=hash_token(code),
            expires_at=expires_at,
        )
        notifications.send_email(
            to=account.email,
            subject="Your MUHUZE verification code",
            body=(
                f"Your verification code is {code}. "
                f"It expires in {settings.otp_expire_minutes} minutes."
            ),
        )

    async def confirm_email_verification(self, account: Account, *, code: str) -> None:
        stored = await self.verification_codes.get_valid(
            account_id=account.id,
            purpose=VerificationPurpose.EMAIL_VERIFICATION,
            code_hash=hash_token(code),
        )
        if stored is None:
            raise InvalidVerificationCodeError()
        await self.verification_codes.mark_verified(stored)
        await self.accounts.mark_verified(account)


class PasswordResetService:
    """Business rules for the forgot-password flow."""

    def __init__(
        self,
        accounts: AccountRepository,
        password_reset_tokens: PasswordResetTokenRepository,
        refresh_tokens: RefreshTokenRepository,
    ) -> None:
        self.accounts = accounts
        self.password_reset_tokens = password_reset_tokens
        self.refresh_tokens = refresh_tokens

    async def request_password_reset(self, *, email: str) -> None:
        """Always succeeds from the caller's point of view, whether or not the
        email belongs to an account — an error here would leak which emails
        are registered."""
        account = await self.accounts.get_by_email(email)
        if account is None:
            return
        raw_token = generate_password_reset_token()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.password_reset_token_expire_minutes
        )
        await self.password_reset_tokens.create(
            account_id=account.id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
        )
        notifications.send_email(
            to=account.email,
            subject="Reset your MUHUZE password",
            body=(
                f"Your password reset token is {raw_token}. "
                f"It expires in {settings.password_reset_token_expire_minutes} minutes."
            ),
        )

    async def reset_password(self, *, raw_token: str, new_password: str) -> None:
        stored = await self.password_reset_tokens.get_valid_by_token_hash(
            hash_token(raw_token)
        )
        if stored is None:
            raise InvalidPasswordResetTokenError()

        account = await self.accounts.get_by_id(stored.account_id)
        if account is None:
            raise InvalidPasswordResetTokenError()

        await self.password_reset_tokens.mark_used(stored)
        await self.accounts.update_password(
            account, password_hash=hash_password(new_password)
        )
        # A leaked/guessed old password should not let anyone keep using
        # sessions issued before the reset.
        await self.refresh_tokens.revoke_all_for_account(account.id)


class AuthorizationService:
    """Business rules for role/permission lookups and management. Managing
    roles/permissions (as opposed to just checking them) is gated by
    require_role("admin") at the router layer, not here — this service
    assumes the caller is already authorized to make the change."""

    def __init__(
        self, authorization: AuthorizationRepository, accounts: AccountRepository
    ) -> None:
        self.authorization = authorization
        self.accounts = accounts

    async def get_my_authorization(
        self, account_id: uuid.UUID
    ) -> tuple[list[str], list[str]]:
        roles = await self.authorization.get_role_names(account_id)
        permissions = await self.authorization.get_permission_codes(account_id)
        return roles, permissions

    async def has_role(self, account_id: uuid.UUID, *role_names: str) -> bool:
        roles = await self.authorization.get_role_names(account_id)
        return bool(set(role_names) & set(roles))

    async def has_permission(self, account_id: uuid.UUID, *codes: str) -> bool:
        permissions = await self.authorization.get_permission_codes(account_id)
        return bool(set(codes) & set(permissions))

    async def list_roles(self) -> list[Role]:
        return await self.authorization.get_all_roles()

    async def list_permissions(self) -> list[Permission]:
        return await self.authorization.get_all_permissions()

    async def assign_role_to_account(
        self, account_id: uuid.UUID, role_name: str
    ) -> None:
        if await self.accounts.get_by_id(account_id) is None:
            raise AccountNotFoundError()
        role = await self.authorization.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError()
        await self.authorization.assign_role(account_id=account_id, role_id=role.id)

    async def revoke_role_from_account(
        self, account_id: uuid.UUID, role_name: str
    ) -> None:
        if await self.accounts.get_by_id(account_id) is None:
            raise AccountNotFoundError()
        role = await self.authorization.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError()
        await self.authorization.revoke_role(account_id=account_id, role_id=role.id)

    async def assign_permission_to_role(
        self, role_name: str, permission_code: str
    ) -> None:
        role = await self.authorization.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError()
        permission = await self.authorization.get_permission_by_code(permission_code)
        if permission is None:
            raise PermissionNotFoundError()
        await self.authorization.assign_permission_to_role(
            role_id=role.id, permission_id=permission.id
        )

    async def revoke_permission_from_role(
        self, role_name: str, permission_code: str
    ) -> None:
        role = await self.authorization.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError()
        permission = await self.authorization.get_permission_by_code(permission_code)
        if permission is None:
            raise PermissionNotFoundError()
        await self.authorization.revoke_permission_from_role(
            role_id=role.id, permission_id=permission.id
        )
