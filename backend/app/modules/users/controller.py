import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.repository import ProfileRepository
from app.modules.users.schemas import ProfileResponse, ProfileUpsertRequest
from app.modules.users.service import ProfileService


class ProfileController:
    """Translates HTTP requests/responses to and from the profile service."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = ProfileService(ProfileRepository(db))

    async def get_my_profile(self, account_id: uuid.UUID) -> ProfileResponse:
        profile = await self.service.get_my_profile(account_id)
        return ProfileResponse.model_validate(profile)

    async def upsert_my_profile(
        self, account_id: uuid.UUID, payload: ProfileUpsertRequest
    ) -> ProfileResponse:
        profile = await self.service.upsert_profile(
            account_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
        )
        return ProfileResponse.model_validate(profile)
