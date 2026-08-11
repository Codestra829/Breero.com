from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenRequest,
    TokenResponse,
    UserRead,
)
from app.domains.auth.service import AuthService

router = APIRouter()


def client(request: Request) -> tuple[str | None, str | None]:
    return request.headers.get("user-agent"), request.client.host if request.client else None


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest, request: Request, session: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    return await AuthService(session).register(data, *client(request))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, request: Request, session: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    return await AuthService(session).login(data, *client(request))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest, request: Request, session: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    return await AuthService(session).refresh(data.refresh_token, *client(request))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: RefreshRequest, session: Annotated[AsyncSession, Depends(get_db)]) -> None:
    await AuthService(session).logout(data.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await AuthService(session).logout_all(user)


@router.post("/password/forgot", response_model=MessageResponse)
async def forgot(
    data: ForgotPasswordRequest, session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    await AuthService(session).forgot_password(str(data.email))
    return MessageResponse(message="If the account exists, reset instructions have been sent")


@router.post("/password/reset", response_model=MessageResponse)
async def reset(
    data: ResetPasswordRequest, session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    await AuthService(session).reset_password(data.token, data.new_password)
    return MessageResponse(message="Password reset")


@router.post("/password/change", response_model=MessageResponse)
async def change(
    data: ChangePasswordRequest,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    await AuthService(session).change_password(user, data.current_password, data.new_password)
    return MessageResponse(message="Password changed; active sessions revoked")


@router.post("/email/verify", response_model=MessageResponse)
async def verify(
    data: TokenRequest, session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    await AuthService(session).verify_email(data.token)
    return MessageResponse(message="Email verified")


@router.post("/email/resend-verification", response_model=MessageResponse)
async def resend(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    await AuthService(session).resend_verification(user)
    return MessageResponse(message="Verification sent if required")


@router.get("/me", response_model=UserRead)
async def me(user: Annotated[User, Depends(current_user)]) -> User:
    return user
