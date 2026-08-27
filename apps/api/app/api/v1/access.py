import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.access_service import AccessService
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import AccessRole, Department, TenantScope, User, UserRole
from app.domains.auth.schemas import AccessProfileUpdate, PortalContext

router = APIRouter()
admin_only = require_roles(UserRole.admin)


@router.get("/catalog")
async def access_catalog(_: Annotated[User, Depends(admin_only)]) -> dict[str, list[str]]:
    return {
        "roles": [role.value for role in AccessRole],
        "departments": [department.value for department in Department],
        "tenant_scopes": [scope.value for scope in TenantScope],
    }


@router.get("/users/{user_id}", response_model=PortalContext)
async def user_access(
    user_id: uuid.UUID,
    _: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PortalContext:
    target = await session.scalar(select(User).where(User.id == user_id))
    if not target:
        raise HTTPException(404, "User not found")
    return await AccessService(session).context(target)


@router.put("/users/{user_id}", response_model=PortalContext)
async def replace_user_access(
    user_id: uuid.UUID,
    data: AccessProfileUpdate,
    _: Annotated[User, Depends(admin_only)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PortalContext:
    return await AccessService(session).replace_assignments(
        user_id=user_id,
        brand_key=data.brand_key,
        assignments=data.assignments,
    )
