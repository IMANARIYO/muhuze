import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import (
    Account,
    AccountRole,
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    VerificationCode,
)


class AccountRepository:
    """Data access for accounts. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_email(self, email: str) -> Account | None:
        result = await self.db.execute(select(Account).where(Account.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def create(
        self, *, email: str, phone: str | None, password_hash: str
    ) -> Account:
        account = Account(email=email, phone=phone, password_hash=password_hash)
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def mark_verified(self, account: Account) -> None:
        account.is_verified = True
        await self.db.flush()

    async def update_password(self, account: Account, *, password_hash: str) -> None:
        account.password_hash = password_hash
        await self.db.flush()


class RefreshTokenRepository:
    """Data access for refresh tokens. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, account_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            account_id=account_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(refresh_token)
        await self.db.flush()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(UTC)
        await self.db.flush()

    async def revoke_all_for_account(self, account_id: uuid.UUID) -> None:
        """Used on password reset: invalidate every session, since the old
        password (and anything issued under it) can no longer be trusted."""
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.account_id == account_id, RefreshToken.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now(UTC))
        )


class VerificationCodeRepository:
    """Data access for verification codes. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        account_id: uuid.UUID,
        purpose: str,
        code_hash: str,
        expires_at: datetime,
    ) -> VerificationCode:
        code = VerificationCode(
            account_id=account_id,
            purpose=purpose,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        self.db.add(code)
        await self.db.flush()
        await self.db.refresh(code)
        return code

    async def get_valid(
        self, *, account_id: uuid.UUID, purpose: str, code_hash: str
    ) -> VerificationCode | None:
        result = await self.db.execute(
            select(VerificationCode).where(
                VerificationCode.account_id == account_id,
                VerificationCode.purpose == purpose,
                VerificationCode.code_hash == code_hash,
                VerificationCode.verified_at.is_(None),
                VerificationCode.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def mark_verified(self, code: VerificationCode) -> None:
        code.verified_at = datetime.now(UTC)
        await self.db.flush()


class PasswordResetTokenRepository:
    """Data access for password reset tokens. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, account_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        token = PasswordResetToken(
            account_id=account_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(token)
        await self.db.flush()
        await self.db.refresh(token)
        return token

    async def get_valid_by_token_hash(
        self, token_hash: str
    ) -> PasswordResetToken | None:
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(UTC)
        await self.db.flush()


class AuthorizationRepository:
    """Data access for roles/permissions and their assignments. No business
    rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def assign_role(self, *, account_id: uuid.UUID, role_id: uuid.UUID) -> None:
        exists = await self.db.execute(
            select(AccountRole).where(
                AccountRole.account_id == account_id, AccountRole.role_id == role_id
            )
        )
        if exists.scalar_one_or_none() is not None:
            return
        self.db.add(AccountRole(account_id=account_id, role_id=role_id))
        await self.db.flush()

    async def get_role_names(self, account_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(
            select(Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return list(result.scalars().all())

    async def get_permission_codes(self, account_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(AccountRole, AccountRole.role_id == RolePermission.role_id)
            .where(AccountRole.account_id == account_id)
        )
        return list(result.scalars().all())

    async def get_role_by_id(self, role_id: uuid.UUID) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> list[Role]:
        result = await self.db.execute(select(Role).order_by(Role.name))
        return list(result.scalars().all())

    async def revoke_role(self, *, account_id: uuid.UUID, role_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(AccountRole).where(
                AccountRole.account_id == account_id, AccountRole.role_id == role_id
            )
        )
        account_role = result.scalar_one_or_none()
        if account_role is not None:
            await self.db.delete(account_role)
            await self.db.flush()

    async def get_permission_by_code(self, code: str) -> Permission | None:
        result = await self.db.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def get_all_permissions(self) -> list[Permission]:
        result = await self.db.execute(select(Permission).order_by(Permission.code))
        return list(result.scalars().all())

    async def assign_permission_to_role(
        self, *, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        exists = await self.db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        if exists.scalar_one_or_none() is not None:
            return
        self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))
        await self.db.flush()

    async def revoke_permission_from_role(
        self, *, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        result = await self.db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        role_permission = result.scalar_one_or_none()
        if role_permission is not None:
            await self.db.delete(role_permission)
            await self.db.flush()
