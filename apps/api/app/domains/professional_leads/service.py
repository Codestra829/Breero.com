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

    @staticmethod
    def _eligible(vendor: Vendor, lead: ProfessionalLead) -> bool:
        capabilities = {str(item).lower() for item in (vendor.capabilities or [])}
        return lead.service_category.lower() in capabilities

    async def available(self, vendor: Vendor) -> list[ProfessionalLead]:
        now = datetime.now(UTC)
        rows = list(
            (
                await self.session.scalars(
                    select(ProfessionalLead).where(
                        ProfessionalLead.status == LeadStatus.AVAILABLE,
                        (ProfessionalLead.expires_at.is_(None) | (ProfessionalLead.expires_at > now)),
                    )
                )
            ).all()
        )
        return [lead for lead in rows if self._eligible(vendor, lead)]

    async def get(self, lead_id: uuid.UUID, vendor: Vendor) -> ProfessionalLead:
        lead = await self.session.get(ProfessionalLead, lead_id)
        if not lead or lead.status != LeadStatus.AVAILABLE or not self._eligible(vendor, lead):
            raise DomainError("LEAD_NOT_FOUND", "Opportunity was not found", 404)
        if lead.expires_at and lead.expires_at <= datetime.now(UTC):
            raise DomainError("LEAD_NOT_FOUND", "Opportunity was not found", 404)
        return lead

    async def purchase(self, lead_id: uuid.UUID, vendor_id: uuid.UUID, key: str) -> LeadPurchase:
        if not settings.stripe_enabled:
            raise DomainError("PAYMENT_PROVIDER_UNAVAILABLE", "Lead purchasing is unavailable until payment configuration is complete", 503)
        vendor = await self.session.get(Vendor, vendor_id)
        if not vendor or vendor.status != VendorStatus.ACTIVE:
            raise DomainError("PROVIDER_NOT_ELIGIBLE", "Provider is not eligible for this opportunity", 403)
        existing = await self.session.scalar(select(LeadPurchase).where(LeadPurchase.vendor_id == vendor_id, LeadPurchase.idempotency_key == key))
        if existing:
            if existing.lead_id != lead_id:
                raise DomainError("IDEMPOTENCY_CONFLICT", "Key already used for another purchase", 409)
            return existing
        lead = await self.session.scalar(select(ProfessionalLead).where(ProfessionalLead.id == lead_id).with_for_update())
        if not lead or lead.status != LeadStatus.AVAILABLE:
            raise DomainError("LEAD_UNAVAILABLE", "Opportunity is no longer available", 409)
        if lead.expires_at and lead.expires_at <= datetime.now(UTC):
            raise DomainError("LEAD_UNAVAILABLE", "Opportunity has expired", 409)
        if not self._eligible(vendor, lead):
            raise DomainError("PROVIDER_NOT_ELIGIBLE", "Provider is not eligible for this opportunity", 403)
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
        deadline = purchase.created_at + timedelta(hours=72)
        existing = await self.session.scalar(
            select(LeadDispute).where(
                LeadDispute.purchase_id == purchase.id,
                LeadDispute.reason == reason,
            )
        )
        if existing:
            return existing
        dispute = LeadDispute(
            purchase_id=purchase.id,
            vendor_id=vendor_id,
            reason=reason,
            details=details,
            status=DisputeStatus.OPEN,
            deadline_at=deadline,
        )
        self.session.add(dispute)
        await self.session.commit()
        return dispute

    async def get_dispute(self, lead_id: uuid.UUID, dispute_id: uuid.UUID, vendor_id: uuid.UUID) -> LeadDispute:
        dispute = await self.session.scalar(select(LeadDispute).join(LeadPurchase).where(LeadPurchase.lead_id == lead_id, LeadDispute.id == dispute_id, LeadDispute.vendor_id == vendor_id))
        if not dispute:
            raise DomainError("DISPUTE_NOT_FOUND", "Dispute was not found", 404)
        return dispute
