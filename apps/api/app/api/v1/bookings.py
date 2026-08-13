import hashlib
import hmac
import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.domains.booking.models import Booking
from app.domains.booking.schemas import (
    BookingConfirmation,
    BookingCreateRequest,
    BookingCreateResponse,
)
from app.domains.booking.service import BookingService
from app.domains.payments.models import Payment, PaymentPurpose
from app.domains.payments.schemas import PaymentIntentCreate, PaymentView
from app.domains.payments.service import PaymentService
from app.integrations.stripe import StripeAdapter

router = APIRouter()


def to_response(booking: Booking) -> BookingCreateResponse:
    return BookingCreateResponse(
        id=booking.id,
        reference=booking.reference,
        status=booking.status,
        total_amount=booking.total_amount,
        currency=booking.currency,
        window_start=booking.window_start,
        window_end=booking.window_end,
        payment_required=False,
        guest_confirmation_token=getattr(booking, "guest_confirmation_token", None),
    )


@router.post("", response_model=BookingCreateResponse, status_code=201)
async def create_booking(
    payload: BookingCreateRequest,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("booking-create", 10, 60)),
) -> BookingCreateResponse:
    return to_response(await BookingService(session).create(payload, idempotency_key))


async def guest_booking(
    session: AsyncSession, booking_id: uuid.UUID, authorization: str
) -> Booking:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Guest confirmation token is required")
    token = authorization.removeprefix("Bearer ").strip()
    if len(token) < 32:
        raise HTTPException(401, "Invalid guest confirmation token")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    booking = await session.get(Booking, booking_id)
    if (
        not booking
        or not hmac.compare_digest(booking.guest_confirmation_token_hash, token_hash)
        or booking.guest_confirmation_revoked_at is not None
        or booking.guest_confirmation_expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(403, "Guest confirmation token is invalid or expired")
    return booking


@router.post("/{booking_id}/payment", response_model=PaymentView, status_code=201)
async def prepare_booking_payment(
    booking_id: uuid.UUID,
    authorization: str = Header(alias="Authorization"),
    idempotency_key: str = Header(min_length=8, max_length=255, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("guest-payment-prepare", 10, 60)),
) -> PaymentView:
    if not settings.stripe_enabled:
        raise HTTPException(404, "Online payments are disabled; all work requires a quote")
    booking = await guest_booking(session, booking_id, authorization)
    amount_minor = int(
        (booking.total_amount * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    return await PaymentService(session, StripeAdapter.from_environment()).create_intent(
        PaymentIntentCreate(
            booking_id=booking.id,
            payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
            amount_minor=amount_minor,
            currency=booking.currency,
        ),
        idempotency_key,
    )


@router.get("/{booking_id}/confirmation", response_model=BookingConfirmation)
async def booking_confirmation(
    booking_id: uuid.UUID,
    authorization: str = Header(alias="Authorization"),
    session: AsyncSession = Depends(get_db),
    _rate_limit: None = Depends(rate_limit("guest-booking-confirmation", 30, 60)),
) -> BookingConfirmation:
    booking = await guest_booking(session, booking_id, authorization)
    payment = await session.scalar(
        select(Payment)
        .where(Payment.booking_id == booking.id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    payment_status = payment.status.value if payment else "disabled"
    if booking.status.value == "CONFIRMED":
        next_action = "confirmed"
    elif booking.status.value in {"EXPIRED", "CANCELLED"}:
        next_action = "booking_unavailable"
    elif booking.status.value == "PENDING_MANUAL_DISPATCH":
        next_action = "await_manual_dispatch"
    elif booking.status.value == "TENTATIVE_HOLD":
        next_action = "await_operator_confirmation"
    else:
        next_action = "await_provider_match"
    return BookingConfirmation(
        booking_id=booking.id,
        reference=booking.reference,
        booking_status=booking.status,
        payment_status=payment_status,
        window_start=booking.window_start,
        window_end=booking.window_end,
        amount_minor=int(booking.total_amount * 100),
        currency=booking.currency,
        next_action=next_action,
        payment_required=False,
        quote_required=True,
    )
