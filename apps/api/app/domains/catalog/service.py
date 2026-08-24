from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.models import Service, ServiceQuestion
from app.domains.catalog.repository import CatalogRepository
from app.domains.catalog.schemas import ServiceDetail, ServiceRead, ServiceWrite


class CatalogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.catalog = CatalogRepository(session)

    async def list_services(self) -> list[ServiceRead]:
        return [ServiceRead.model_validate(item) for item in await self.catalog.list_active()]

    async def detail(self, identifier: str) -> ServiceDetail:
        service = await self.catalog.active_detail(identifier)
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        result = ServiceDetail.model_validate(service)
        result.questions = [
            question
            for question, model in zip(result.questions, service.questions, strict=True)
            if model.is_active
        ]
        return result

    async def create(self, data: ServiceWrite) -> ServiceDetail:
        if await self.catalog.by_slug(data.slug):
            raise HTTPException(status_code=409, detail="Service slug already exists")
        values = data.model_dump(exclude={"questions"})
        service = Service(
            **values,
            questions=[ServiceQuestion(**question.model_dump()) for question in data.questions],
        )
        await self.catalog.add(service)
        await self.session.commit()
        return ServiceDetail.model_validate(service)
