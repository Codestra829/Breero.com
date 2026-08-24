import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domains.common.models import TimestampMixin, UUIDPrimaryKeyMixin


class PrivacyRequestStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    VERIFYING = "VERIFYING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DENIED = "DENIED"
    APPEALED = "APPEALED"


class PrivacyRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "privacy_requests"
    request_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    status: Mapped[PrivacyRequestStatus] = mapped_column(
        Enum(PrivacyRequestStatus, name="privacy_request_status"),
        nullable=False,
        default=PrivacyRequestStatus.RECEIVED,
    )
    verification_state: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING")
    receipt_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    jurisdiction: Mapped[str | None] = mapped_column(String(3))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class ConsentEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "consent_events"
    destination_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source_ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    disclosure_text: Mapped[str] = mapped_column(Text, nullable=False)
    policy_versions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class Suppression(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "communication_suppressions"
    __table_args__ = (UniqueConstraint("destination_hash", "channel", "purpose"),)
    destination_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
