import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_dependencies import (
    get_auth_service,
    get_client_info,
    get_current_auth,
)
from app.modules.auth.auth_schema import (
    AccountResponse,
    ChangePasswordRequest,
    EmailVerificationConfirmRequest,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    TokenResponse,
)
from app.modules.auth.auth_service import AuthenticatedAccount, AuthService, ClientInfo
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentAuthDep = Annotated[AuthenticatedAccount, Depends(get_current_auth)]
ClientInfoDep = Annotated[ClientInfo, Depends(get_client_info)]


@auth_router.post(
    "/register", response_model=APIResponse[AccountResponse], status_code=status.HTTP_201_CREATED
)
async def register(payload: RegisterRequest, service: AuthServiceDep) -> JSONResponse:
    """Create an account and email it a verification code. The account can't
    log in until the code is confirmed."""
    account = await service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone=payload.phone,
    )
    return success_response(
        data=AccountResponse.model_validate(account),
        message="Account created. Enter the verification code sent to your email.",
        status_code=status.HTTP_201_CREATED,
    )


@auth_router.post("/email/verification/request", response_model=APIResponse[None])
async def request_email_verification(
    payload: EmailVerificationRequest, service: AuthServiceDep
) -> JSONResponse:
    """Send a new verification code. The response is the same whether or not
    the email belongs to an unverified account."""
    await service.request_email_verification(email=payload.email)
    return success_response(
        message="If that email belongs to an unverified account, a new code has been sent"
    )


@auth_router.post("/email/verification/confirm", response_model=APIResponse[None])
async def confirm_email_verification(
    payload: EmailVerificationConfirmRequest, service: AuthServiceDep
) -> JSONResponse:
    """Confirm the emailed code. The account can log in afterwards."""
    await service.confirm_email_verification(email=payload.email, code=payload.code)
    return success_response(message="Email verified. You can now log in.")


@auth_router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    payload: LoginRequest, service: AuthServiceDep, client: ClientInfoDep
) -> JSONResponse:
    """Exchange email and password for an access token and a refresh token."""
    tokens = await service.login(email=payload.email, password=payload.password, client=client)
    return success_response(data=TokenResponse.model_validate(tokens), message="Login successful")


@auth_router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh(
    payload: RefreshTokenRequest, service: AuthServiceDep, client: ClientInfoDep
) -> JSONResponse:
    """Exchange a refresh token for a new pair. The refresh token sent here
    stops working; using it again ends every session of the account."""
    tokens = await service.refresh(refresh_token=payload.refresh_token, client=client)
    return success_response(data=TokenResponse.model_validate(tokens), message="Token refreshed")


@auth_router.post("/logout", response_model=APIResponse[None])
async def logout(payload: RefreshTokenRequest, service: AuthServiceDep) -> JSONResponse:
    """End the session that owns this refresh token."""
    await service.logout(refresh_token=payload.refresh_token)
    return success_response(message="Logged out")


@auth_router.post("/logout-all", response_model=APIResponse[None])
async def logout_all(auth: CurrentAuthDep, service: AuthServiceDep) -> JSONResponse:
    """End every session of the caller's account, on every device."""
    await service.logout_all(account_id=auth.account.id)
    return success_response(message="Logged out of all devices")


@auth_router.get("/me", response_model=APIResponse[AccountResponse])
async def get_me(auth: CurrentAuthDep) -> JSONResponse:
    """The caller's own account."""
    return success_response(
        data=AccountResponse.model_validate(auth.account), message="Account retrieved"
    )


@auth_router.get("/sessions", response_model=APIResponse[Page[SessionResponse]])
async def list_sessions(
    pagination: Annotated[PaginationParams, Query()], auth: CurrentAuthDep, service: AuthServiceDep
) -> JSONResponse:
    """The caller's active sessions, most recently used first."""
    page = await service.list_sessions(auth=auth, pagination=pagination)
    return success_response(data=page, message="Sessions retrieved")


@auth_router.delete("/sessions/{session_id}", response_model=APIResponse[None])
async def revoke_session(
    session_id: uuid.UUID, auth: CurrentAuthDep, service: AuthServiceDep
) -> JSONResponse:
    """End one of the caller's own sessions."""
    await service.revoke_session(account_id=auth.account.id, session_id=session_id)
    return success_response(message="Session ended")


@auth_router.post("/password/change", response_model=APIResponse[None])
async def change_password(
    payload: ChangePasswordRequest, auth: CurrentAuthDep, service: AuthServiceDep
) -> JSONResponse:
    """Change the password. Every other session is ended; this one stays."""
    await service.change_password(
        auth=auth,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return success_response(message="Password changed")


@auth_router.post("/password/forgot", response_model=APIResponse[None])
async def forgot_password(payload: ForgotPasswordRequest, service: AuthServiceDep) -> JSONResponse:
    """Email a password reset link. The response is the same whether or not
    the email is registered."""
    await service.request_password_reset(email=payload.email)
    return success_response(message="If that email is registered, a reset link has been sent")


@auth_router.post("/password/reset", response_model=APIResponse[None])
async def reset_password(payload: ResetPasswordRequest, service: AuthServiceDep) -> JSONResponse:
    """Set a new password with the token from the reset email. Every session
    of the account is ended."""
    await service.reset_password(token=payload.token, new_password=payload.new_password)
    return success_response(message="Password reset. You can now log in.")
