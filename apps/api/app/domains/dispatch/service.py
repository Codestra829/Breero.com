import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.jobs.models import JobEvent, JobStatus
from app.domains.jobs.repository import JobRepository
from app.domains.workforce.models import Worker

from .models import Assignment, AssignmentStatus, DispatchOffer, OfferStatus
from .repository import DispatchRepository


class DispatchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DispatchRepository(session)
        self.jobs = JobRepository(session)

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
        candidates = await self.repo.candidate_workers([], limit=10)
        if not candidates:
            if job.status != JobStatus.MATCHING:
                previous: JobStatus = job.status
                job.status = JobStatus.MATCHING
                self.jobs.add_event(
                    JobEvent(
                        job_id=job.id,
                        from_status=previous,
                        to_status=job.status,
                        actor_id=actor_id,
                        actor_type="system",
                        reason="no_candidates",
                    )
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
        previous = job.status
        job.status = JobStatus.OFFERED
        job.version += 1
        self.jobs.add_event(
            JobEvent(
                job_id=job.id,
                from_status=previous,
                to_status=job.status,
                actor_id=actor_id,
                actor_type="system",
                reason="offers_created",
                metadata_={"count": len(offers), "round": round_number},
            )
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
        self.session.add(
            Assignment(
                job_id=job.id,
                offer_id=offer.id,
                vendor_id=vendor_id,
                worker_id=worker.id,
                status=AssignmentStatus.ACTIVE,
                assigned_by=actor_id,
            )
        )
        job.vendor_id, job.worker_id = vendor_id, worker.id
        previous, job.status = job.status, JobStatus.ASSIGNED
        job.version += 1
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
        self.jobs.add_event(
            JobEvent(
                job_id=job.id,
                from_status=previous,
                to_status=job.status,
                actor_id=actor_id,
                actor_type="vendor",
                reason="offer_accepted",
            )
        )
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(409, "Job was assigned concurrently") from exc
        return offer

    async def manual_assign(self, job_id, vendor_id, worker_id, actor_id, reason) -> Assignment:
        job = await self.jobs.get(job_id, lock=True)
        worker = await self.session.scalar(
            select(Worker).where(
                Worker.id == worker_id, Worker.vendor_id == vendor_id, Worker.available.is_(True)
            )
        )
        if not job:
            raise HTTPException(404, "Job not found")
        if not worker:
            raise HTTPException(409, "Worker is unavailable or belongs to another vendor")
        if job.status not in {JobStatus.CREATED, JobStatus.MATCHING, JobStatus.OFFERED}:
            raise HTTPException(409, "Job is not assignable")
        assignment = Assignment(
            job_id=job.id,
            vendor_id=vendor_id,
            worker_id=worker_id,
            status=AssignmentStatus.ACTIVE,
            assigned_by=actor_id,
        )
        self.session.add(assignment)
        previous, job.status = job.status, JobStatus.ASSIGNED
        job.vendor_id, job.worker_id, job.version = vendor_id, worker_id, job.version + 1
        worker.available = False
        self.jobs.add_event(
            JobEvent(
                job_id=job.id,
                from_status=previous,
                to_status=job.status,
                actor_id=actor_id,
                actor_type="operations",
                reason=reason,
            )
        )
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
