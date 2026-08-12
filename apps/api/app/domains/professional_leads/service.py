import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import DomainError
from app.domains.workforce.models import Vendor, VendorStatus

from .models import (
    DisputeStatus,
    LeadDispute,
    LeadPurchase,
    LeadPurchaseStatus,
    LeadStatus,
    ProfessionalLead,
)


class ProfessionalLeadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def available(self) -> list[ProfessionalLead]:
        return list((await self.session.scalars(select(ProfessionalLead).where(ProfessionalLead.status == LeadStatus.AVAILABLE))).all())

    async def purchase(self, lead_id: uuid.UUID, vendor_id: uuid.UUID, key: str) -> LeadPurchase:
        if not settings.stripe_enabled:
            raise DomainError("PAYMENT_PROVIDER_UNAVAILABLE", "Lead purchasing is unavailable until payment configuration is complete", 503)
        vendor = await self.session.get(Vendor, vendor_id)
        if not vendor or vendor.status != VendorStatus.ACTIVE:
            raise DomainError("PROVIDER_NOT_ELIGIBLE", "Provider is not eligible for this opportunity", 403)
        existing = await self.session.scalar(select(LeadPurchase).where(LeadPurchase.vendor_id == vendor_id, LeadPurchase.idempotency_key == key))
        if existing:
            return existing
        lead = await self.session.scalar(select(ProfessionalLead).where(ProfessionalLead.id == lead_id).with_for_update())
        if not lead or lead.status != LeadStatus.AVAILABLE:
            raise DomainError("LEAD_UNAVAILABLE", "Opportunity is no longer available", 409)
        purchase = LeadPurchase(lead_id=lead.id, vendor_id=vendor_id, idempotency_key=key, price_minor=lead.price_minor, currency=lead.currency, status=LeadPurchaseStatus.PENDING_PAYMENT)
        lead.status = LeadStatus.PURCHASED
        lead.purchased_by_vendor_id = vendor_id
        self.session.add(purchase)
        await self.session.commit()
        return purchase

    async def dispute(self, lead_id: uuid.UUID, vendor_id: uuid.UUID, reason: str, details: str) -> LeadDispute:
        purchase = await self.session.scalar(select(LeadPurchase).where(LeadPurchase.lead_id == lead_id, LeadPurchase.vendor_id == vendor_id))
        if not purchase:
            raise DomainError("PURCHASE_NOT_FOUND", "Purchased opportunity was not found", 404)
        if datetime.now(UTC) > purchase.created_at + timedelta(hours=72):
            raise DomainError("DISPUTE_WINDOW_EXPIRED", "The 72-hour dispute window has expired", 422)
        dispute = LeadDispute(purchase_id=purchase.id, vendor_id=vendor_id, reason=reason, details=details, status=DisputeStatus.OPEN)
        self.session.add(dispute)
        await self.session.commit()
        return dispute

    async def get_dispute(self, lead_id: uuid.UUID, dispute_id: uuid.UUID, vendor_id: uuid.UUID) -> LeadDispute:
        dispute = await self.session.scalar(select(LeadDispute).join(LeadPurchase).where(LeadPurchase.lead_id == lead_id, LeadDispute.id == dispute_id, LeadDispute.vendor_id == vendor_id))
        if not dispute:
            raise DomainError("DISPUTE_NOT_FOUND", "Dispute was not found", 404)
        return dispute
