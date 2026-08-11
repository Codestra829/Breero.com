import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.catalog.models import Service


class CatalogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> list[Service]:
        result = await self.session.scalars(
            select(Service)
            .where(Service.is_active.is_(True))
            .order_by(Service.sort_order, Service.name)
        )
        return list(result)

    async def active_detail(self, identifier: str) -> Service | None:
        try:
            service_id = uuid.UUID(identifier)
            condition = Service.id == service_id
        except ValueError:
            condition = Service.slug == identifier
        return await self.session.scalar(
            select(Service)
            .options(selectinload(Service.questions))
            .where(condition, Service.is_active.is_(True))
        )

    async def by_slug(self, slug: str) -> Service | None:
        return await self.session.scalar(select(Service).where(Service.slug == slug))

    async def add(self, service: Service) -> Service:
        self.session.add(service)
        await self.session.flush()
        return service
