import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domains.booking.models import Address
from app.domains.common.outbox import AuditLog
from app.domains.jobs.models import JobStatus
from app.domains.jobs.repository import JobRepository
from app.domains.jobs.service import JobService
from app.domains.workforce.models import Worker

from .models import Assignment, AssignmentStatus, DispatchOffer, OfferStatus
from .repository import DispatchRepository


class DispatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DispatchRepository(session)
        self.jobs = JobRepository(session)
        self.job_service = JobService(session)

    async def match(
        self, job_id: uuid.UUID, actor_id: uuid.UUID | None = None
    ) -> list[DispatchOffer]:
        job = await self.jobs.get(job_id, lock=True)
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status not in {JobStatus.CREATED, JobStatus.MATCHING, JobStatus.OFFERED}:
            raise HTTPException(409, "Job cannot be matched in its current state")
        existing = await self.repo.offers_for_job(job_id)
        round_number = max((offer.round for offer in existing), default=0) + 1
        address = await self.session.get(Address, job.address_id)
        if not address or not address.validated_at or not address.postal_code:
            self.job_service.apply_transition(
                job, JobStatus.MATCHING, actor_id, "system", "address_not_validated"
            )
            await self.session.commit()
            return []
        candidates = await self.repo.candidate_workers(
            [str(job.service_id)], address.postal_code, job.scheduled_start.date(), limit=10
        )
        zone = ZoneInfo(address.timezone or "UTC")
        candidates = [
            candidate
            for candidate in candidates
            if self._supports_working_hours(
                candidate[0].working_hours,
                job.scheduled_start.astimezone(zone),
                job.scheduled_end.astimezone(zone),
            )
        ]
        if not candidates:
            if job.status != JobStatus.MATCHING:
                self.job_service.apply_transition(
                    job, JobStatus.MATCHING, actor_id, "system", "no_candidates"
                )
            await self.session.commit()
            return []
        now = datetime.now(UTC)
        offers = []
        for rank, (vendor, worker) in enumerate(candidates):
            offer = DispatchOffer(
                job_id=job.id,
                vendor_id=vendor.id,
                worker_id=worker.id,
                status=OfferStatus.PENDING,
                round=round_number,
                score=1000 - rank,
                score_detail={"availability": 100, "capability": 100},
                expires_at=now + timedelta(minutes=15),
            )
            self.session.add(offer)
            offers.append(offer)
        if job.status == JobStatus.CREATED:
            self.job_service.apply_transition(
                job, JobStatus.MATCHING, actor_id, "system", "matching_started"
            )
        self.job_service.apply_transition(
            job,
            JobStatus.OFFERED,
            actor_id,
            "system",
            "offers_created",
            {"count": len(offers), "round": round_number},
        )
        await self.session.commit()
        return offers

    async def decide_offer(
        self,
        offer_id: uuid.UUID,
        vendor_id: uuid.UUID,
        accept: bool,
        worker_id: uuid.UUID | None,
        actor_id: uuid.UUID,
    ) -> DispatchOffer:
        offer = await self.repo.get_offer(offer_id, lock=True)
        if not offer:
            raise HTTPException(404, "Offer not found")
        if offer.vendor_id != vendor_id:
            raise HTTPException(403, "Offer belongs to another vendor")
        if offer.status != OfferStatus.PENDING:
            raise HTTPException(409, "Offer is no longer pending")
        if offer.expires_at <= datetime.now(UTC):
            offer.status = OfferStatus.EXPIRED
            await self.session.commit()
            raise HTTPException(409, "Offer has expired")
        offer.responded_at = datetime.now(UTC)
        if not accept:
            offer.status = OfferStatus.DECLINED
            await self.session.commit()
            return offer
        selected_worker = worker_id or offer.worker_id
        worker = await self.session.scalar(
            select(Worker).where(
                Worker.id == selected_worker,
                Worker.vendor_id == vendor_id,
                Worker.available.is_(True),
            )
        )
        if not worker:
            raise HTTPException(409, "Selected worker is unavailable")
        job = await self.jobs.get(offer.job_id, lock=True)
        if not job or job.status not in {JobStatus.OFFERED, JobStatus.MATCHING}:
            raise HTTPException(409, "Job is no longer assignable")
        offer.status = OfferStatus.ACCEPTED
        if not settings.automatic_provider_assignment_enabled:
            self.session.add(
                AuditLog(
                    actor_id=actor_id,
                    action="provider.recommendation.accepted",
                    resource_type="job",
                    resource_id=job.id,
                    metadata_json={"vendor_id": str(vendor_id), "operator_confirmation_required": True},
                    created_at=datetime.now(UTC),
                )
            )
            await self.session.commit()
            return offer
        assignment = Assignment(
                job_id=job.id,
                offer_id=offer.id,
                vendor_id=vendor_id,
                worker_id=worker.id,
                status=AssignmentStatus.ACTIVE,
                assigned_by=actor_id,
                scheduled_start=job.scheduled_start,
                scheduled_end=job.scheduled_end,
            )
        self.session.add(assignment)
        self.session.add(
            AuditLog(
                actor_id=actor_id,
                action="assignment.create",
                resource_type="job",
                resource_id=job.id,
                metadata_json={"vendor_id": str(vendor_id), "worker_id": str(worker.id)},
                created_at=datetime.now(UTC),
            )
        )
        job.vendor_id, job.worker_id = vendor_id, worker.id
        self.job_service.apply_transition(
            job, JobStatus.ASSIGNED, actor_id, "vendor", "offer_accepted"
        )
        worker.available = False
        await self.session.execute(
            update(DispatchOffer)
            .where(
                DispatchOffer.job_id == job.id,
                DispatchOffer.id != offer.id,
                DispatchOffer.status == OfferStatus.PENDING,
            )
            .values(status=OfferStatus.WITHDRAWN)
        )
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(409, "Job was assigned concurrently") from exc
        return offer

    async def manual_assign(self, job_id, vendor_id, worker_id, actor_id, reason) -> Assignment:
        job = await self.jobs.get(job_id, lock=True)
        if job:
            await self.session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                {"key": f"worker-schedule:{worker_id}"},
            )
        address = await self.session.get(Address, job.address_id) if job else None
        worker = await self.session.scalar(
            select(Worker).where(
                Worker.id == worker_id, Worker.vendor_id == vendor_id, Worker.available.is_(True)
            )
        )
        if not job:
            raise HTTPException(404, "Job not found")
        if not worker:
            raise HTTPException(409, "Worker is unavailable or belongs to another vendor")
        from app.domains.workforce.models import Vendor, VendorStatus

        vendor = await self.session.get(Vendor, vendor_id)
        today = job.scheduled_start.date()
        if (
            not address
            or not address.validated_at
            or not vendor
            or vendor.status != VendorStatus.ACTIVE
            or address.postal_code not in (vendor.covered_postal_codes or [])
            or str(job.service_id) not in (vendor.capabilities or [])
            or not vendor.license_valid_until
            or vendor.license_valid_until < today
            or not vendor.insurance_valid_until
            or vendor.insurance_valid_until < today
            or not self._supports_working_hours(
                vendor.working_hours,
                job.scheduled_start.astimezone(ZoneInfo(address.timezone or "UTC")),
                job.scheduled_end.astimezone(ZoneInfo(address.timezone or "UTC")),
            )
        ):
            raise HTTPException(409, "Provider is not qualified for this service address and date")
        if job.status not in {JobStatus.CREATED, JobStatus.MATCHING, JobStatus.OFFERED}:
            raise HTTPException(409, "Job is not assignable")
        assignment = Assignment(
            job_id=job.id,
            vendor_id=vendor_id,
            worker_id=worker_id,
            status=AssignmentStatus.ACTIVE,
            assigned_by=actor_id,
            scheduled_start=job.scheduled_start,
            scheduled_end=job.scheduled_end,
        )
        self.session.add(assignment)
        self.session.add(
            AuditLog(
                actor_id=actor_id,
                action="assignment.create",
                resource_type="job",
                resource_id=job.id,
                metadata_json={
                    "vendor_id": str(vendor_id),
                    "worker_id": str(worker_id),
                    "reason": reason,
                },
                created_at=datetime.now(UTC),
            )
        )
        self.job_service.apply_transition(
            job, JobStatus.ASSIGNED, actor_id, "operations", reason
        )
        job.vendor_id, job.worker_id = vendor_id, worker_id
        worker.available = False
        from app.domains.booking.models import Booking, BookingStatus

        booking = await self.session.get(Booking, job.booking_id)
        if booking:
            if booking.hold_expires_at and booking.hold_expires_at <= datetime.now(UTC):
                raise HTTPException(409, "Tentative slot hold has expired")
            booking.status = BookingStatus.SCHEDULED
            booking.confirmed_at = datetime.now(UTC)
            booking.confirmed_by = actor_id
            booking.scheduling_version += 1
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(409, "Worker has an overlapping active assignment") from exc
        await self.session.refresh(assignment)
        return assignment

    async def reassign(self, job_id, vendor_id, worker_id, actor_id, reason) -> Assignment:
        job = await self.jobs.get(job_id, lock=True)
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status != JobStatus.ASSIGNED:
            raise HTTPException(409, "Only an assigned job can be reassigned")
        current = await self.session.scalar(
            select(Assignment).where(
                Assignment.job_id == job.id, Assignment.status == AssignmentStatus.ACTIVE
            ).with_for_update()
        )
        if not current:
            raise HTTPException(409, "Active assignment is missing")
        previous_worker = await self.session.get(Worker, current.worker_id)
        current.status = AssignmentStatus.RELEASED
        current.released_at = datetime.now(UTC)
        if previous_worker:
            previous_worker.available = True
        job.vendor_id = None
        job.worker_id = None
        self.job_service.apply_transition(
            job, JobStatus.MATCHING, actor_id, "operations", f"reassignment: {reason}"
        )
        await self.session.flush()
        return await self.manual_assign(job.id, vendor_id, worker_id, actor_id, reason)

    @staticmethod
    def _supports_working_hours(
        working_hours: dict, local_start: datetime, local_end: datetime
    ) -> bool:
        windows = (working_hours or {}).get(str(local_start.weekday()), [])
        for start_text, end_text in windows:
            try:
                start_value = time.fromisoformat(start_text)
                end_value = time.fromisoformat(end_text)
            except (TypeError, ValueError):
                continue
            if start_value <= local_start.time().replace(tzinfo=None) and local_end.time().replace(
                tzinfo=None
            ) <= end_value:
                return True
        return False
