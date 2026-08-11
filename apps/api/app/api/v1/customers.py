import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.bookings import to_response
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.booking.repository import BookingRepository
from app.domains.booking.schemas import BookingResponse, CustomerBookingList

router = APIRouter()


@router.get("/me/bookings", response_model=CustomerBookingList)
async def my_bookings(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CustomerBookingList:
    repository = BookingRepository(session)
    customer = await repository.customer_for_email(user.email)
    return CustomerBookingList(
        items=[]
        if not customer
        else [to_response(item) for item in await repository.customer_bookings(customer.id)]
    )


@router.get("/me/bookings/{booking_id}", response_model=BookingResponse)
async def my_booking(
    booking_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BookingResponse:
    repository = BookingRepository(session)
    customer = await repository.customer_for_email(user.email)
    if not customer:
        raise HTTPException(status_code=404, detail="Booking not found")
    bookings = await repository.customer_bookings(customer.id)
    booking = next((item for item in bookings if item.id == booking_id), None)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return to_response(booking)
