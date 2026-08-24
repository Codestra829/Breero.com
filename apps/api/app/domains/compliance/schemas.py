import uuid
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, model_validator

PrivacyType = Literal[
    "access",
    "correction",
    "deletion",
    "portability",
    "opt_out_sale_sharing",
    "opt_out_targeted_ads",
    "appeal",
]


class PrivacyRequestCreate(BaseModel):
    requestType: PrivacyType
    email: EmailStr
    jurisdiction: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    gpc: bool = False


class PrivacyRequestAccepted(BaseModel):
    request_id: uuid.UUID
    status: str
    receipt_token: str
    due_at: str


class PrivacyRequestView(BaseModel):
    request_id: uuid.UUID
    request_type: str
    status: str
    verification_state: str
    due_at: str
    completed_at: str | None


class CommunicationPreferenceCreate(BaseModel):
    destination: str = Field(min_length=5, max_length=320)
    transactionalEmail: bool = False
    transactionalSms: bool = False
    marketingEmail: bool = False
    marketingSms: bool = False
    source_url: AnyHttpUrl
    disclosure_text: str = Field(min_length=10, max_length=4000)
    policy_versions: dict[str, str]

    @model_validator(mode="after")
    def valid_destination(self):
        if "@" in self.destination and self.transactionalSms:
            raise ValueError("SMS requires a phone number")
        if "@" not in self.destination and self.transactionalEmail:
            raise ValueError("email requires an email address")
        return self


class PreferenceAccepted(BaseModel):
    status: Literal["RECORDED"] = "RECORDED"
    suppression_active: bool


class SmsRevocation(BaseModel):
    phone: str = Field(min_length=7, max_length=40)
    message: str = Field(min_length=1, max_length=500)
