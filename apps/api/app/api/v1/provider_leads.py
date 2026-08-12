import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.professional_leads.schemas import (
    DisputeCreate,
    DisputeRead,
    LeadRead,
    PurchaseRead,
)
from app.domains.professional_leads.service import ProfessionalLeadService
from app.domains.workforce.models import Vendor

router = APIRouter()


async def provider_context(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(UserRole.vendor_admin))],
) -> Vendor:
    vendor = await session.scalar(select(Vendor).where(Vendor.owner_user_id == user.id))
    if not vendor:
        raise DomainError("PROVIDER_CONTEXT_REQUIRED", "Provider account is not linked to a business", 403)
    return vendor


@router.get("", response_model=list[LeadRead])
async def list_leads(session: Annotated[AsyncSession, Depends(get_db)], _: Annotated[Vendor, Depends(provider_context)]):
    return await ProfessionalLeadService(session).available()


@router.post("/{lead_id}/purchase", response_model=PurchaseRead)
async def purchase_lead(lead_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db)], vendor: Annotated[Vendor, Depends(provider_context)], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
    if not idempotency_key:
        raise DomainError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key is required", 400)
    return await ProfessionalLeadService(session).purchase(lead_id, vendor.id, idempotency_key)


@router.post("/{lead_id}/disputes", response_model=DisputeRead)
async def create_dispute(lead_id: uuid.UUID, data: DisputeCreate, session: Annotated[AsyncSession, Depends(get_db)], vendor: Annotated[Vendor, Depends(provider_context)]):
    return await ProfessionalLeadService(session).dispute(lead_id, vendor.id, data.reason, data.details)


@router.get("/{lead_id}/disputes/{dispute_id}", response_model=DisputeRead)
async def get_dispute(lead_id: uuid.UUID, dispute_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_db)], vendor: Annotated[Vendor, Depends(provider_context)]):
    return await ProfessionalLeadService(session).get_dispute(lead_id, dispute_id, vendor.id)
