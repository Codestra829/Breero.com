import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EarningStatus(str, enum.Enum):
    PENDING = "PENDING"
    AVAILABLE = "AVAILABLE"
    BATCHED = "BATCHED"
    PAID = "PAID"
    REVERSED = "REVERSED"


class PayoutStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"


class VendorEarning(Base):
    __tablename__ = "vendor_earnings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), unique=True)
    gross_minor: Mapped[int] = mapped_column(Integer)
    fee_minor: Mapped[int] = mapped_column(Integer)
    net_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[EarningStatus] = mapped_column(
        Enum(EarningStatus, name="earning_status"), index=True
    )
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payout_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payout_batches.id"), index=True
    )
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
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
