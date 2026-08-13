import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, field_validator

from app.domains.common.us import US_STATES_AND_DC


class TrackingFields(BaseModel):
    source_url: AnyHttpUrl
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=120)
    utm_content: str | None = Field(default=None, max_length=120)
    utm_term: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, max_length=16)
    customer_timezone: str | None = Field(default=None, max_length=64)
    transactional_contact_allowed: bool = True
    marketing_consent: bool = False
    sms_consent: bool = False
    email_consent: bool = False
    consent_timestamp: str | None = Field(default=None, max_length=40)
    consent_source: str | None = Field(default=None, max_length=120)
    policy_version: str | None = Field(default=None, max_length=40)
    company: str = Field(default="", max_length=0, exclude=True)


class ServiceRequestCreate(TrackingFields):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=40)
    service_id: uuid.UUID | None = None
    service_slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    service_description: str = Field(min_length=5, max_length=4000)
    address_line1: str = Field(min_length=3, max_length=240)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(pattern=r"^[A-Z]{2}$")
    postal_code: str = Field(pattern=r"^\d{5}(?:-\d{4})?$")
    requested_date: date | None = None
    requested_timing: str | None = Field(default=None, max_length=200)
    contact_preference: Literal["email", "phone", "text"]

    @field_validator("state")
    @classmethod
    def supported_us_state(cls, value: str) -> str:
        if value not in US_STATES_AND_DC:
            raise ValueError("Service requests require a U.S. state or Washington, D.C.")
        return value


class ContactCreate(TrackingFields):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str | None = Field(default=None, min_length=7, max_length=40)
    category: Literal["booking_help", "service_issue", "billing", "general", "business", "privacy_request", "provider_question"]
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=5000)


class ProviderInterestCreate(TrackingFields):
    business_name: str = Field(min_length=2, max_length=200)
    contact_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=40)
    business_website: AnyHttpUrl | None = None
    service_categories: list[str] = Field(min_length=1, max_length=20)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(pattern=r"^[A-Z]{2}$")
    postal_code: str = Field(pattern=r"^\d{5}(?:-\d{4})?$")
    license_details: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=3000)


class SubmissionAccepted(BaseModel):
    request_id: uuid.UUID
    status: Literal["REQUEST_ACCEPTED"] = "REQUEST_ACCEPTED"
    downstream_status: str


class DispatcherAuditEntry(BaseModel):
    action: str
    actor_id: uuid.UUID | None
    metadata: dict[str, Any]
    created_at: datetime


class DispatcherQueueItem(BaseModel):
    request_id: uuid.UUID
    submission_type: str
    created_at: datetime
    request_age_seconds: int
    required_follow_up: bool
    customer_timezone: str | None
    address_verification_state: str | None
    manual_dispatch_state: str | None
    provider_assigned: bool
    contact_attempts: list[dict[str, Any]]
    downstream_status: str
    payload: dict[str, Any]
    audit_history: list[DispatcherAuditEntry]


class DispatcherQueueUpdate(BaseModel):
    manual_dispatch_state: Literal[
        "PENDING_MANUAL_DISPATCH",
        "CUSTOMER_CONTACT_PENDING",
        "CUSTOMER_CONTACTED",
        "ADDRESS_VALIDATION_PENDING",
        "PROVIDER_MATCH_PENDING",
        "QUOTE_COORDINATION_PENDING",
        "CANCELLED",
        "CLOSED",
    ] | None = None
    address_verification_state: Literal[
        "PENDING_MANUAL_VALIDATION", "MANUALLY_VERIFIED", "REJECTED"
    ] | None = None
    address_timezone: str | None = Field(default=None, max_length=64)
    contact_outcome: Literal[
        "NO_ANSWER", "VOICEMAIL", "CUSTOMER_REACHED", "FOLLOW_UP_REQUESTED", "CANCELLED"
    ] | None = None
    required_follow_up: bool | None = None
    note: str | None = Field(default=None, max_length=1000)
