from pydantic import BaseModel


class PublicCapabilities(BaseModel):
    request_intake: bool
    instant_booking: bool
    online_payments: bool
    automatic_assignment: bool
    provider_self_service: bool
    marketplace_matching: bool
    messaging: bool
    reviews: bool
