from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.catalog.schemas import QuestionRead, ServiceDetail, ServiceRead, ServiceWrite
from app.domains.catalog.service import CatalogService

router = APIRouter()


@router.get("")
async def list_services(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ServiceRead]:
    return await CatalogService(session).list_services()


@router.get("/{service_id}", response_model=ServiceDetail)
async def get_service(
    service_id: str, session: Annotated[AsyncSession, Depends(get_db)]
) -> ServiceDetail:
    return await CatalogService(session).detail(service_id)


@router.get("/{service_id}/questions")
async def list_service_questions(
    service_id: str, session: Annotated[AsyncSession, Depends(get_db)]
) -> list[QuestionRead]:
    return (await CatalogService(session).detail(service_id)).questions


@router.post("", response_model=ServiceDetail, status_code=201)
async def create_service(
    data: ServiceWrite,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.operations, UserRole.admin))],
) -> ServiceDetail:
    return await CatalogService(session).create(data)
