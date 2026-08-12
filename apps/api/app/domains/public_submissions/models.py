import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SubmissionType(str, enum.Enum):
    SERVICE_REQUEST = "SERVICE_REQUEST"
    CONTACT = "CONTACT"
    PROVIDER_INTEREST = "PROVIDER_INTEREST"


class DownstreamStatus(str, enum.Enum):
    PENDING = "PENDING"
    PENDING_CONFIGURATION = "PENDING_CONFIGURATION"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class PublicSubmission(Base):
    __tablename__ = "public_submissions"
    __table_args__ = (
        UniqueConstraint("submission_type", "idempotency_key", name="uq_public_submission_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_type: Mapped[SubmissionType] = mapped_column(
        Enum(SubmissionType, name="public_submission_type"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    normalized_phone: Mapped[str | None] = mapped_column(String(40), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    downstream_status: Mapped[DownstreamStatus] = mapped_column(
        Enum(DownstreamStatus, name="public_submission_downstream_status"), nullable=False
    )
    source_ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
