import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import DisputeStatus, LeadPurchaseStatus, LeadStatus


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    service_category: str
    location_summary: str
    qualification_criteria: dict
    price_minor: int
    currency: str
    policy_version: str
    status: LeadStatus
    opportunity_disclosure: str = "Access to a customer opportunity; not a guaranteed job, sale, contract, appointment outcome, or revenue."


class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    lead_id: uuid.UUID
    vendor_id: uuid.UUID
    price_minor: int
    currency: str
    status: LeadPurchaseStatus


class DisputeCreate(BaseModel):
    reason: Literal["invalid_contact", "duplicate_charged_lead", "wrong_service_category", "material_qualification_mismatch", "documented_platform_defect"]
    details: str = Field(min_length=10, max_length=4000)


class DisputeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    purchase_id: uuid.UUID
    vendor_id: uuid.UUID
    reason: str
    details: str
    status: DisputeStatus
    created_at: datetime
