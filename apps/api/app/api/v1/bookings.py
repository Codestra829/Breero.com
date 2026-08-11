from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()


class CustomerInput(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


class BookingWindow(BaseModel):
    start: datetime
    end: datetime


class BookingAnswer(BaseModel):
    question_id: str
    value: str


class BookingCreateRequest(BaseModel):
    service_id: str
    customer: CustomerInput
    address_id: str
    window: BookingWindow
    answers: list[BookingAnswer] = []


@router.post("", status_code=201)
async def create_booking(payload: BookingCreateRequest) -> dict:
    return {
        "status": "PENDING_PAYMENT",
        "booking_id": None,
        "payment_required": True,
    }
