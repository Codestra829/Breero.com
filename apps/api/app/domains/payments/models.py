import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    REQUIRES_ACTION = "requires_action"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentPurpose(str, enum.Enum):
    BOOKING_DIAGNOSTIC = "BOOKING_DIAGNOSTIC"
    QUOTE_ADDITIONAL_WORK = "QUOTE_ADDITIONAL_WORK"
    PROFESSIONAL_LEAD = "PROFESSIONAL_LEAD"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_booking_id_created_at", "booking_id", "created_at"),
        UniqueConstraint("provider", "provider_payment_id", name="uq_payments_provider_payment_id"),
        CheckConstraint(
            "(payment_purpose = 'BOOKING_DIAGNOSTIC' AND booking_id IS NOT NULL AND quote_id IS NULL AND lead_purchase_id IS NULL) OR (payment_purpose = 'QUOTE_ADDITIONAL_WORK' AND booking_id IS NULL AND quote_id IS NOT NULL AND lead_purchase_id IS NULL) OR (payment_purpose = 'PROFESSIONAL_LEAD' AND booking_id IS NULL AND quote_id IS NULL AND lead_purchase_id IS NOT NULL)",
            name="valid_payment_reference",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    quote_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    lead_purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("professional_lead_purchases.id"), unique=True, index=True
    )
    payment_purpose: Mapped[PaymentPurpose] = mapped_column(
        Enum(PaymentPurpose, name="payment_purpose"),
        nullable=False,
        default=PaymentPurpose.BOOKING_DIAGNOSTIC,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="stripe")
    provider_payment_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=PaymentStatus.CREATED,
    )
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    captured_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_client_secret: Mapped[str | None] = mapped_column(Text)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (
        UniqueConstraint("payment_id", "idempotency_key", name="uq_refunds_payment_key"),
        UniqueConstraint("provider_refund_id", name="uq_refunds_provider_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, name="refund_status"), nullable=False
    )
    provider_refund_id: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_payment_events_provider_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL")
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdempotencyRecord(Base):
    __tablename__ = "payment_idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "operation", "idempotency_key", name="uq_payment_idempotency_operation_key"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
