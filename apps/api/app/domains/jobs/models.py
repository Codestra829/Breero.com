import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStatus(str, enum.Enum):
    CREATED = "CREATED"
    MATCHING = "MATCHING"
    OFFERED = "OFFERED"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE = "EN_ROUTE"
    ON_SITE = "ON_SITE"
    DIAGNOSING = "DIAGNOSING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkRequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    service_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    address_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), index=True)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    diagnostic_notes: Mapped[str | None] = mapped_column(Text)
    completion_notes: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class JobEvent(Base):
    __tablename__ = "job_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[JobStatus | None] = mapped_column(Enum(JobStatus, name="job_status"))
    to_status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_type: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkRequest(Base):
    __tablename__ = "work_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    status: Mapped[WorkRequestStatus] = mapped_column(
        Enum(WorkRequestStatus, name="work_request_status"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    line_items: Mapped[list] = mapped_column(JSONB)
    subtotal_minor: Mapped[int] = mapped_column(Integer)
    tax_minor: Mapped[int] = mapped_column(Integer)
    total_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    payment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    customer_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
