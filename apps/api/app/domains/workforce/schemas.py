import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import VendorStatus, WorkerStatus


class VendorCreate(BaseModel):
    legal_name: str = Field(min_length=1, max_length=180)
    display_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=32)
    capabilities: list[str] = []
    service_radius_meters: int = Field(default=40000, ge=1000, le=500000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordinates_are_a_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    legal_name: str
    display_name: str
    email: str
    phone: str
    status: VendorStatus
    capabilities: list
    service_radius_meters: int


class VendorStatusUpdate(BaseModel):
    status: VendorStatus


class WorkerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=32)
    skills: list[str] = []
    user_id: uuid.UUID | None = None


class WorkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vendor_id: uuid.UUID
    user_id: uuid.UUID | None
    first_name: str
    last_name: str
    email: str
    phone: str
    status: WorkerStatus
    skills: list
    available: bool


class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: int | None = Field(default=None, ge=0, le=10000)
