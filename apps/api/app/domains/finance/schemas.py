import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import AdjustmentType, CompensationMethod, EarningStatus, PayoutStatus


class CompensationPlanCreate(BaseModel):
    vendor_id: uuid.UUID
    name: str = Field(min_length=1, max_length=160)
    method: CompensationMethod
    fixed_minor: int | None = Field(default=None, ge=0)
    percentage_bps: int | None = Field(default=None, ge=0, le=10_000)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    hold_days: int = Field(default=7, ge=0, le=365)
    effective_from: datetime


class CompensationPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vendor_id: uuid.UUID
    name: str
    method: CompensationMethod
    currency: str
    hold_days: int
    active: bool


class EarningAdjustmentCreate(BaseModel):
    amount_minor: int
    adjustment_type: AdjustmentType
    reason: str = Field(min_length=1, max_length=1000)
    idempotency_key: str = Field(min_length=1, max_length=128)


class EarningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vendor_id: uuid.UUID
    job_id: uuid.UUID
    gross_minor: int
    fee_minor: int
    net_minor: int
    currency: str
    status: EarningStatus
    available_at: datetime


class PayoutBatchCreate(BaseModel):
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    vendor_id: uuid.UUID | None = None


class PayoutBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reference: str
    status: PayoutStatus
    currency: str
    total_minor: int
    earning_count: int
    approved_by: uuid.UUID | None
    created_at: datetime


class PayoutFailure(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
