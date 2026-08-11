from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.domains.auth.service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest, session: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    return await AuthService(session).register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest, session: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    return await AuthService(session).login(data)


@router.get("/me", response_model=UserRead)
async def me(user: Annotated[User, Depends(current_user)]) -> User:
    return user
