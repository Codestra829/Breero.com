import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompensationMethod(str, enum.Enum):
    FIXED_MINOR = "FIXED_MINOR"
    PERCENTAGE = "PERCENTAGE"
    SERVICE_RATE = "SERVICE_RATE"


class EarningStatus(str, enum.Enum):
    PENDING = "PENDING"
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    APPROVED = "APPROVED"
    BATCHED = "BATCHED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"


class AdjustmentType(str, enum.Enum):
    REFUND = "REFUND"
    DISPUTE = "DISPUTE"
    MANUAL = "MANUAL"
    REVERSAL = "REVERSAL"


class PayoutStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VendorCompensationPlan(Base):
    __tablename__ = "vendor_compensation_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    method: Mapped[CompensationMethod] = mapped_column(
        Enum(CompensationMethod, name="compensation_method")
    )
    fixed_minor: Mapped[int | None] = mapped_column(Integer)
    percentage_bps: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    hold_days: Mapped[int] = mapped_column(Integer, default=7)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VendorServiceCompensation(Base):
    __tablename__ = "vendor_service_compensations"
    __table_args__ = (UniqueConstraint("plan_id", "service_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendor_compensation_plans.id", ondelete="CASCADE"), index=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    rate_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")


class CompensationSnapshot(Base):
    """Immutable evidence of the exact rule used for an earning."""

    __tablename__ = "compensation_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    method: Mapped[CompensationMethod] = mapped_column(
        Enum(CompensationMethod, name="compensation_method", create_type=False)
    )
    rule_json: Mapped[dict] = mapped_column(JSONB)
    gross_minor: Mapped[int] = mapped_column(Integer)
    compensation_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    hold_days: Mapped[int] = mapped_column(Integer)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class VendorEarning(Base):
    __tablename__ = "vendor_earnings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), unique=True)
    compensation_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("compensation_snapshots.id"), unique=True
    )
    gross_minor: Mapped[int] = mapped_column(Integer)
    fee_minor: Mapped[int] = mapped_column(Integer)
    net_minor: Mapped[int] = mapped_column(Integer)
    adjustment_total_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[EarningStatus] = mapped_column(
        Enum(EarningStatus, name="earning_status"), index=True
    )
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payout_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payout_batches.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def payable_minor(self) -> int:
        return self.net_minor + self.adjustment_total_minor


class EarningAdjustment(Base):
    __tablename__ = "earning_adjustments"
    __table_args__ = (UniqueConstraint("earning_id", "idempotency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    earning_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vendor_earnings.id", ondelete="RESTRICT"), index=True
    )
    adjustment_type: Mapped[AdjustmentType] = mapped_column(
        Enum(AdjustmentType, name="earning_adjustment_type")
    )
    amount_minor: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PayoutBatch(Base):
    __tablename__ = "payout_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[PayoutStatus] = mapped_column(
        Enum(PayoutStatus, name="payout_status"), index=True
    )
    currency: Mapped[str] = mapped_column(String(3))
    total_minor: Mapped[int] = mapped_column(Integer)
    earning_count: Mapped[int] = mapped_column(Integer)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_transfer_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    provider_status: Mapped[str | None] = mapped_column(String(80))
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
