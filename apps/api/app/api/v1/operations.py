import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.auth.dependencies import require_roles
from app.domains.auth.models import User, UserRole
from app.domains.booking.scheduling import SchedulingService
from app.domains.booking.schemas import (
    BookingCancellationRequest,
    BookingRescheduleRequest,
    BookingResponse,
)
from app.domains.dispatch.schemas import AssignmentRead, ManualAssignment, OfferRead
from app.domains.dispatch.service import DispatchService
from app.domains.workforce.repository import WorkforceRepository
from app.domains.workforce.schemas import VendorRead, VendorStatusUpdate

router = APIRouter()


@router.post("/bookings/{booking_id}/reschedule", response_model=BookingResponse)
async def reschedule_booking(
    booking_id: uuid.UUID,
    payload: BookingRescheduleRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await SchedulingService(session).reschedule(booking_id, payload, user.id)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    payload: BookingCancellationRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await SchedulingService(session).cancel(
        booking_id, payload.reason, payload.expected_version, user.id
    )


@router.post("/jobs/{job_id}/match", response_model=list[OfferRead])
async def match_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).match(job_id, user.id)


@router.post("/jobs/{job_id}/assign", response_model=AssignmentRead, status_code=201)
async def assign_job(
    job_id: uuid.UUID,
    payload: ManualAssignment,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).manual_assign(
        job_id, payload.vendor_id, payload.worker_id, user.id, payload.reason
    )


@router.post("/jobs/{job_id}/reassign", response_model=AssignmentRead, status_code=201)
async def reassign_job(
    job_id: uuid.UUID,
    payload: ManualAssignment,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    return await DispatchService(session).reassign(
        job_id, payload.vendor_id, payload.worker_id, user.id, payload.reason
    )


@router.patch("/vendors/{vendor_id}/status", response_model=VendorRead)
async def set_vendor_status(
    vendor_id: uuid.UUID,
    payload: VendorStatusUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.operations, UserRole.admin)),
):
    from fastapi import HTTPException

    vendor = await WorkforceRepository(session).get_vendor(vendor_id, lock=True)
    if not vendor:
        raise HTTPException(404, "Vendor not found")
    vendor.status = payload.status
    await session.commit()
    await session.refresh(vendor)
    return vendor
