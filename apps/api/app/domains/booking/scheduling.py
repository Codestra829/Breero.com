import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.outbox import AuditLog, EventStatus, IntegrationEvent
from app.domains.dispatch.models import Assignment, AssignmentStatus
from app.domains.jobs.models import Job, JobStatus
from app.domains.jobs.service import JobService

from .models import Booking, BookingStatus
from .repository import BookingRepository
from .schemas import AvailabilitySearchRequest, BookingRescheduleRequest
from .service import AvailabilityService


class SchedulingService:
    """Operator-controlled booking lifecycle; no method performs payment activity."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BookingRepository(session)

    async def reschedule(
        self, booking_id: uuid.UUID, payload: BookingRescheduleRequest, actor_id: uuid.UUID
    ) -> Booking:
        booking = await self.session.scalar(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        )
        if not booking:
            raise HTTPException(404, "Booking not found")
        if booking.scheduling_version != payload.expected_version:
            raise HTTPException(409, "Booking changed; reload before rescheduling")
        if booking.status in {BookingStatus.CANCELLED, BookingStatus.EXPIRED}:
            raise HTTPException(409, "Booking cannot be rescheduled in its current state")
        if payload.window.start >= payload.window.end or payload.window.start <= datetime.now(UTC):
            raise HTTPException(422, "Requested window must be in the future")
        address = await self.repo.address(booking.address_id)
        if not address or not address.validated_at or not address.timezone:
            raise HTTPException(409, "A validated address and time zone are required")
        local_start = payload.window.start.astimezone(ZoneInfo(address.timezone))
        local_end = payload.window.end.astimezone(ZoneInfo(address.timezone))
        if local_start.date() != local_end.date() or local_start.hour < 7 or local_end.hour > 19:
            raise HTTPException(422, "Requested time must be between 7:00 AM and 7:00 PM local time")
        if local_start.weekday() == 6 and not payload.urgent:
            raise HTTPException(422, "Sunday scheduling is limited to urgent home-service requests")

        await self.repo.lock_slot(booking.service_id, payload.window.start, payload.window.end)
        slot_available = False
        if address.service_area_id:
            slots = await AvailabilityService(self.session).search(
                AvailabilitySearchRequest(
                    service_id=booking.service_id,
                    address_id=booking.address_id,
                    date_from=local_start.date(),
                    date_to=local_start.date(),
                )
            )
            slot_available = any(
                slot.start == payload.window.start and slot.end == payload.window.end
                for slot in slots
            )

        previous = {
            "start": booking.window_start.isoformat(),
            "end": booking.window_end.isoformat(),
            "status": booking.status.value,
        }
        booking.window_start = payload.window.start
        booking.window_end = payload.window.end
        booking.status = (
            BookingStatus.TENTATIVE_HOLD
            if slot_available
            else BookingStatus.PENDING_MANUAL_DISPATCH
        )
        booking.hold_expires_at = (
            datetime.now(UTC) + timedelta(minutes=15) if slot_available else None
        )
        booking.confirmed_at = None
        booking.confirmed_by = None
        booking.scheduling_version += 1
        job = await self.session.scalar(select(Job).where(Job.booking_id == booking.id).with_for_update())
        if job:
            job.scheduled_start = booking.window_start
            job.scheduled_end = booking.window_end
            job.version += 1
            assignment = await self.session.scalar(
                select(Assignment).where(
                    Assignment.job_id == job.id, Assignment.status == AssignmentStatus.ACTIVE
                )
            )
            if assignment:
                assignment.scheduled_start = booking.window_start
                assignment.scheduled_end = booking.window_end
        self._audit_event(
            booking,
            actor_id,
            "booking.rescheduled",
            {"previous": previous, "reason": payload.reason, "slot_available": slot_available},
        )
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(409, "Provider has an overlapping assignment") from exc
        await self.session.refresh(booking)
        return booking

    async def cancel(
        self, booking_id: uuid.UUID, reason: str, expected_version: int, actor_id: uuid.UUID
    ) -> Booking:
        booking = await self.session.scalar(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        )
        if not booking:
            raise HTTPException(404, "Booking not found")
        if booking.scheduling_version != expected_version:
            raise HTTPException(409, "Booking changed; reload before cancelling")
        if booking.status == BookingStatus.CANCELLED:
            return booking
        if booking.status == BookingStatus.EXPIRED:
            raise HTTPException(409, "Expired booking cannot be cancelled")
        previous = booking.status.value
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason
        booking.hold_expires_at = None
        booking.scheduling_version += 1
        job = await self.session.scalar(select(Job).where(Job.booking_id == booking.id).with_for_update())
        if job and job.status != JobStatus.CANCELLED:
            JobService(self.session).apply_transition(job, JobStatus.CANCELLED, actor_id, "operations", reason)
        self._audit_event(booking, actor_id, "booking.cancelled", {"previous_status": previous, "reason": reason})
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    def _audit_event(
        self, booking: Booking, actor_id: uuid.UUID, event_type: str, metadata: dict
    ) -> None:
        self.session.add(
            AuditLog(
                actor_id=actor_id,
                actor_type="operations",
                action=event_type,
                resource_type="booking",
                resource_id=booking.id,
                metadata_json=metadata,
                created_at=datetime.now(UTC),
            )
        )
        self.session.add(
            IntegrationEvent(
                aggregate_type="booking",
                aggregate_id=booking.id,
                event_type=event_type,
                aggregate_version=booking.scheduling_version,
                idempotency_key=f"{event_type}:{booking.id}:{booking.scheduling_version}",
                payload={
                    "booking_id": str(booking.id),
                    "status": booking.status.value,
                    "scheduling_version": booking.scheduling_version,
                    "payment_required": False,
                },
                status=EventStatus.PENDING,
                attempts=0,
                available_at=datetime.now(UTC),
            )
        )
