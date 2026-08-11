import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import EarningStatus, PayoutStatus


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
