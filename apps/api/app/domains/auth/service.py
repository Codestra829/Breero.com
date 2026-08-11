from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User, UserRole
from app.domains.auth.repository import UserRepository
from app.domains.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.domains.auth.security import (
    TOKEN_TTL_SECONDS,
    create_access_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        email = data.email.lower()
        if await self.users.by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        user = await self.users.add(
            User(
                email=email,
                full_name=data.full_name.strip(),
                password_hash=hash_password(data.password),
                role=UserRole.customer,
            )
        )
        await self.session.commit()
        await self.session.refresh(user)
        return self._token(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.users.by_email(data.email.lower())
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        return self._token(user)

    def _token(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            expires_in=TOKEN_TTL_SECONDS,
            user=UserRead.model_validate(user),
        )
