import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.bookings import to_response
from app.db.session import get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User
from app.domains.booking.models import Address, Booking, BookingStatus, Customer
from app.domains.booking.schemas import BookingResponse
from app.domains.common.outbox import AuditLog
from app.domains.jobs.models import Job, JobStatus, WorkRequest
from app.domains.jobs.schemas import WorkRequestDecision, WorkRequestRead
from app.domains.jobs.service import JobService
from app.domains.payments.models import Payment, PaymentPurpose, PaymentStatus, Refund
from app.domains.payments.schemas import PaymentView

router = APIRouter()


class ProfilePatch(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=160)
    phone: str | None = Field(None, min_length=3, max_length=40)


class ProfileRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str
    email_verified: bool


class AddressInput(BaseModel):
    line1: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=32)
    country_code: str = Field(min_length=2, max_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    line1: str
    city: str
    postal_code: str
    country_code: str


class Page(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class CustomerPaymentRead(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID | None
    quote_id: uuid.UUID | None
    payment_purpose: PaymentPurpose
    provider: str
    status: PaymentStatus
    amount_minor: int
    currency: str
    captured_amount_minor: int
    refunded_amount_minor: int
    failure_code: str | None
    created_at: datetime
    updated_at: datetime


async def customer_for(session: AsyncSession, user: User) -> Customer:
    customer = await session.scalar(select(Customer).where(Customer.user_id == user.id))
    if not customer:
        raise HTTPException(404, "Customer profile not found; verify your email to link it")
    return customer


@router.get("/profile", response_model=ProfileRead)
async def profile(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> ProfileRead:
    customer = await customer_for(session, user)
    return ProfileRead(
        id=customer.id,
        email=user.email,
        full_name=user.full_name,
        phone=customer.phone,
        email_verified=user.email_verified,
    )


@router.patch("/profile", response_model=ProfileRead)
async def update_profile(
    data: ProfilePatch,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileRead:
    customer = await customer_for(session, user)
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
        parts = user.full_name.split(maxsplit=1)
        customer.first_name, customer.last_name = parts[0], parts[1] if len(parts) > 1 else ""
    if data.phone is not None:
        customer.phone = data.phone
    await session.commit()
    return ProfileRead(
        id=customer.id,
        email=user.email,
        full_name=user.full_name,
        phone=customer.phone,
        email_verified=user.email_verified,
    )


@router.get("/addresses", response_model=list[AddressRead])
async def addresses(
    user: Annotated[User, Depends(current_user)], session: Annotated[AsyncSession, Depends(get_db)]
) -> list[Address]:
    customer = await customer_for(session, user)
    return list(
        (
            await session.scalars(
                select(Address)
                .where(Address.customer_id == customer.id)
                .order_by(Address.created_at.desc())
            )
        ).all()
    )


@router.post("/addresses", response_model=AddressRead, status_code=201)
async def add_address(
    data: AddressInput,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Address:
    customer = await customer_for(session, user)
    address = Address(
        customer_id=customer.id,
        formatted_address=f"{data.line1}, {data.postal_code} {data.city}",
        line1=data.line1,
        city=data.city,
        postal_code=data.postal_code,
        country_code=data.country_code.upper(),
        location=WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326),
        geocoding_provider="customer",
    )
    session.add(address)
    await session.commit()
    await session.refresh(address)
    return address


async def owned_address(
    session: AsyncSession, customer: Customer, address_id: uuid.UUID
) -> Address:
    address = await session.scalar(
        select(Address).where(Address.id == address_id, Address.customer_id == customer.id)
    )
    if not address:
        raise HTTPException(404, "Address not found")
    return address


@router.patch("/addresses/{address_id}", response_model=AddressRead)
async def update_address(
    address_id: uuid.UUID,
    data: AddressInput,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Address:
    address = await owned_address(session, await customer_for(session, user), address_id)
    for field in ("line1", "city", "postal_code"):
        setattr(address, field, getattr(data, field))
    address.country_code = data.country_code.upper()
    address.formatted_address = f"{data.line1}, {data.postal_code} {data.city}"
    address.location = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
    await session.commit()
    return address


@router.delete("/addresses/{address_id}", status_code=204)
async def delete_address(
    address_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    address = await owned_address(session, await customer_for(session, user), address_id)
    in_use = await session.scalar(
        select(Booking.id).where(Booking.address_id == address.id).limit(1)
    )
    if in_use:
        raise HTTPException(409, "Address is referenced by a booking")
    await session.delete(address)
    await session.commit()


async def paginate(
    session: AsyncSession, stmt, count_stmt, page: int, size: int
) -> tuple[list, int]:
    return list((await session.scalars(stmt.offset((page - 1) * size).limit(size))).all()), int(
        await session.scalar(count_stmt) or 0
    )


@router.get("/bookings", response_model=Page)
async def bookings(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page:
    c = await customer_for(session, user)
    items, total = await paginate(
        session,
        select(Booking).where(Booking.customer_id == c.id).order_by(Booking.created_at.desc()),
        select(func.count()).select_from(Booking).where(Booking.customer_id == c.id),
        page,
        page_size,
    )
    return Page(
        items=[to_response(x).model_dump() for x in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def booking(
    booking_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BookingResponse:
    c = await customer_for(session, user)
    item = await session.scalar(
        select(Booking).where(Booking.id == booking_id, Booking.customer_id == c.id)
    )
    if not item:
        raise HTTPException(404, "Booking not found")
    return to_response(item)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> BookingResponse:
    customer = await customer_for(session, user)
    item = await session.scalar(
        select(Booking)
        .where(Booking.id == booking_id, Booking.customer_id == customer.id)
        .with_for_update()
    )
    if not item:
        raise HTTPException(404, "Booking not found")
    if item.status == BookingStatus.CANCELLED:
        return to_response(item)
    if item.status not in {
        BookingStatus.REQUESTED,
        BookingStatus.PENDING_MANUAL_DISPATCH,
        BookingStatus.TENTATIVE_HOLD,
        BookingStatus.PROVIDER_ASSIGNED,
        BookingStatus.SCHEDULED,
        BookingStatus.CONFIRMED,
    }:
        raise HTTPException(409, "Booking cannot be cancelled in its current state")
    job = await session.scalar(select(Job).where(Job.booking_id == item.id).with_for_update())
    if job and job.status not in {JobStatus.CREATED, JobStatus.MATCHING, JobStatus.OFFERED}:
        raise HTTPException(409, "Booking can no longer be cancelled online")
    previous = item.status.value
    item.status = BookingStatus.CANCELLED
    item.guest_confirmation_revoked_at = datetime.now(UTC)
    if job:
        JobService(session).apply_transition(
            job, JobStatus.CANCELLED, user.id, "customer", "customer_cancelled_booking"
        )
    session.add(
        AuditLog(
            actor_id=user.id,
            actor_type="customer",
            action="booking.cancel",
            resource_type="booking",
            resource_id=item.id,
            metadata_json={
                "from_status": previous,
                "payment_required": False,
                "refund_required": False,
            },
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()
    return to_response(item)


@router.get("/quotes", response_model=Page)
async def quotes(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page:
    c = await customer_for(session, user)
    base = (
        select(WorkRequest).join(Job, Job.id == WorkRequest.job_id).where(Job.customer_id == c.id)
    )
    items, total = await paginate(
        session,
        base.order_by(WorkRequest.created_at.desc()),
        select(func.count()).select_from(WorkRequest).join(Job).where(Job.customer_id == c.id),
        page,
        page_size,
    )
    return Page(
        items=[WorkRequestRead.model_validate(x).model_dump() for x in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/quotes/{quote_id}", response_model=WorkRequestRead)
async def quote(
    quote_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkRequest:
    c = await customer_for(session, user)
    item = await session.scalar(
        select(WorkRequest).join(Job).where(WorkRequest.id == quote_id, Job.customer_id == c.id)
    )
    if not item:
        raise HTTPException(404, "Quote not found")
    return item


@router.post("/quotes/{quote_id}/decision", response_model=WorkRequestRead)
async def decide_quote(
    quote_id: uuid.UUID,
    payload: WorkRequestDecision,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkRequest:
    customer = await customer_for(session, user)
    return await JobService(session).decide_work_request(quote_id, payload.approve, customer.id)


@router.get("/payments", response_model=Page)
async def payments(
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Page:
    c = await customer_for(session, user)
    owned = (
        select(Payment)
        .outerjoin(Booking, Booking.id == Payment.booking_id)
        .outerjoin(WorkRequest, WorkRequest.id == Payment.quote_id)
        .outerjoin(Job, Job.id == WorkRequest.job_id)
        .where((Booking.customer_id == c.id) | (Job.customer_id == c.id))
    )
    items, total = await paginate(
        session,
        owned.order_by(Payment.created_at.desc()),
        select(func.count()).select_from(owned.subquery()),
        page,
        page_size,
    )
    result = []
    for p in items:
        refunded = int(
            await session.scalar(
                select(func.coalesce(func.sum(Refund.amount_minor), 0)).where(
                    Refund.payment_id == p.id
                )
            )
            or 0
        )
        result.append(
            {
                "id": str(p.id),
                "purpose": p.payment_purpose.value,
                "status": p.status.value,
                "amount_minor": p.amount_minor,
                "captured_amount_minor": p.captured_amount_minor,
                "refunded_amount_minor": refunded,
                "currency": p.currency,
                "created_at": p.created_at.isoformat(),
            }
        )
    return Page(items=result, total=total, page=page, page_size=page_size)


@router.get("/payments/{payment_id}", response_model=CustomerPaymentRead)
async def payment(
    payment_id: uuid.UUID,
    user: Annotated[User, Depends(current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CustomerPaymentRead:
    customer = await customer_for(session, user)
    item = await session.scalar(
        select(Payment)
        .outerjoin(Booking, Booking.id == Payment.booking_id)
        .outerjoin(WorkRequest, WorkRequest.id == Payment.quote_id)
        .outerjoin(Job, Job.id == WorkRequest.job_id)
        .where(
            Payment.id == payment_id,
            (Booking.customer_id == customer.id) | (Job.customer_id == customer.id),
        )
    )
    if not item:
        raise HTTPException(404, "Payment not found")
    refunded = int(
        await session.scalar(
            select(func.coalesce(func.sum(Refund.amount_minor), 0)).where(
                Refund.payment_id == item.id
            )
        )
        or 0
    )
    view = PaymentView.model_validate(item).model_dump()
    return CustomerPaymentRead(**view, refunded_amount_minor=refunded)
