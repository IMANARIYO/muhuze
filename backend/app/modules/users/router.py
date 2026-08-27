from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_account
from app.modules.auth.models import Account
from app.modules.users.controller import ProfileController
from app.modules.users.dependencies import get_profile_controller
from app.modules.users.schemas import ProfileResponse, ProfileUpsertRequest
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_my_profile(
    account: Account = Depends(get_current_account),
    controller: ProfileController = Depends(get_profile_controller),
) -> APIResponse[ProfileResponse]:
    """Get the caller's own profile (name, date of birth). Separate from
    Account — see users/docs for why identity and profile are split."""
    profile = await controller.get_my_profile(account.id)
    return success_response(data=profile, message="Profile retrieved successfully")


@router.put("/me")
async def upsert_my_profile(
    payload: ProfileUpsertRequest,
    account: Account = Depends(get_current_account),
    controller: ProfileController = Depends(get_profile_controller),
) -> APIResponse[ProfileResponse]:
    """Create or fully replace the caller's own profile."""
    profile = await controller.upsert_my_profile(account.id, payload)
    return success_response(data=profile, message="Profile saved successfully")
