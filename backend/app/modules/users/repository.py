import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import Profile


class ProfileRepository:
    """Data access for profiles. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_account_id(self, account_id: uuid.UUID) -> Profile | None:
        result = await self.db.execute(
            select(Profile).where(Profile.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        account_id: uuid.UUID,
        first_name: str,
        last_name: str,
        date_of_birth: date | None,
    ) -> Profile:
        profile = Profile(
            account_id=account_id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update(
        self,
        profile: Profile,
        *,
        first_name: str,
        last_name: str,
        date_of_birth: date | None,
    ) -> Profile:
        profile.first_name = first_name
        profile.last_name = last_name
        profile.date_of_birth = date_of_birth
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
