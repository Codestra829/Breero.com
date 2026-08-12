import uuid
from datetime import date
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, field_validator


class TrackingFields(BaseModel):
    source_url: AnyHttpUrl
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=120)
    utm_content: str | None = Field(default=None, max_length=120)
    utm_term: str | None = Field(default=None, max_length=120)
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
    def texas_only(cls, value: str) -> str:
        if value != "TX":
            raise ValueError("BREERO launch requests are currently limited to approved Texas coverage")
        return value


class ContactCreate(TrackingFields):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str | None = Field(default=None, min_length=7, max_length=40)
    category: Literal["booking_help", "service_issue", "billing", "general", "business"]
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
