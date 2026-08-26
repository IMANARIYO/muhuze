import uuid
from datetime import date

from app.modules.users.exceptions import ProfileNotFoundError
from app.modules.users.models import Profile
from app.modules.users.repository import ProfileRepository


class ProfileService:
    """Business rules for profiles."""

    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    async def get_my_profile(self, account_id: uuid.UUID) -> Profile:
        profile = await self.repository.get_by_account_id(account_id)
        if profile is None:
            raise ProfileNotFoundError()
        return profile

    async def upsert_profile(
        self,
        account_id: uuid.UUID,
        *,
        first_name: str,
        last_name: str,
        date_of_birth: date | None,
    ) -> Profile:
        existing = await self.repository.get_by_account_id(account_id)
        if existing is None:
            return await self.repository.create(
                account_id=account_id,
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
            )
        return await self.repository.update(
            existing,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )
