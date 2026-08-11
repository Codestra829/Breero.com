import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email.lower()))

    async def by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
