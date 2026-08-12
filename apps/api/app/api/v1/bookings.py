from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.booking.models import Booking
from app.domains.booking.schemas import BookingCreateRequest, BookingResponse
from app.domains.booking.service import BookingService

router = APIRouter()


def to_response(booking: Booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        reference=booking.reference,
        status=booking.status.value,
        total_amount=booking.total_amount,
        currency=booking.currency,
        window_start=booking.window_start,
        window_end=booking.window_end,
        payment_required=booking.status.value == "PENDING_PAYMENT",
    )


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    payload: BookingCreateRequest,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("booking-create", 10, 60)),
) -> BookingResponse:
    return to_response(await BookingService(session).create(payload, idempotency_key))
