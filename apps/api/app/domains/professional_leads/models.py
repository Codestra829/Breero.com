import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LeadStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    PURCHASED = "PURCHASED"
    CLOSED = "CLOSED"


class LeadPurchaseStatus(str, enum.Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class ProfessionalLead(Base):
    __tablename__ = "professional_leads"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("public_submissions.id", ondelete="SET NULL"), unique=True, index=True
    )
    service_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location_summary: Mapped[str] = mapped_column(String(200), nullable=False)
    qualification_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus, name="professional_lead_status"), nullable=False, index=True)
    purchased_by_vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LeadPurchase(Base):
    __tablename__ = "professional_lead_purchases"
    __table_args__ = (UniqueConstraint("vendor_id", "idempotency_key", name="uq_lead_purchase_key"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("professional_leads.id"), unique=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[LeadPurchaseStatus] = mapped_column(Enum(LeadPurchaseStatus, name="lead_purchase_status"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LeadDispute(Base):
    __tablename__ = "professional_lead_disputes"
    __table_args__ = (UniqueConstraint("purchase_id", "reason", name="uq_lead_dispute_reason"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("professional_lead_purchases.id"), index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), index=True)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus, name="lead_dispute_status"), nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution: Mapped[str | None] = mapped_column(String(80))
    resolution_reference: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
