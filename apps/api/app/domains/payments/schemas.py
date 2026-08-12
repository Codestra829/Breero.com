import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import PaymentPurpose, PaymentStatus, RefundStatus


class PaymentIntentCreate(BaseModel):
    booking_id: uuid.UUID | None = None
    quote_id: uuid.UUID | None = None
    payment_purpose: PaymentPurpose = PaymentPurpose.BOOKING_DIAGNOSTIC
    amount_minor: int = Field(gt=0, le=100_000_000)
    currency: str = Field(default="usd", min_length=3, max_length=3)
    capture_method: str = Field(default="automatic", pattern="^(automatic|manual)$")
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.lower()


class PaymentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID | None
    quote_id: uuid.UUID | None
    payment_purpose: PaymentPurpose
    provider: str
    status: PaymentStatus
    amount_minor: int
    currency: str
    captured_amount_minor: int
    client_secret: str | None = None
    failure_code: str | None = None
    created_at: datetime
    updated_at: datetime


class CaptureRequest(BaseModel):
    amount_minor: int | None = Field(default=None, gt=0)


class WebhookResult(BaseModel):
    received: bool = True
    duplicate: bool = False
    event_id: str


class ProviderIntent(BaseModel):
    id: str
    status: str
    client_secret: str | None = None
    amount_received: int = 0
    raw: dict[str, Any] = Field(default_factory=dict)


class RefundCreate(BaseModel):
    amount_minor: int | None = Field(default=None, gt=0)
    reason: str | None = Field(default=None, max_length=500)


class RefundView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    payment_id: uuid.UUID
    amount_minor: int
    status: RefundStatus
    provider_refund_id: str | None
    reason: str | None
    created_at: datetime


class ProviderRefund(BaseModel):
    id: str
    status: str
