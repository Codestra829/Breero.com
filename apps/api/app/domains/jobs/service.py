import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Job, JobEvent, JobStatus, WorkRequest, WorkRequestStatus
from .repository import JobRepository
from .schemas import WorkRequestCreate

TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.CREATED: {JobStatus.MATCHING, JobStatus.CANCELLED},
    JobStatus.MATCHING: {JobStatus.OFFERED, JobStatus.ASSIGNED, JobStatus.CANCELLED},
    JobStatus.OFFERED: {JobStatus.MATCHING, JobStatus.ASSIGNED, JobStatus.CANCELLED},
    JobStatus.ASSIGNED: {JobStatus.EN_ROUTE, JobStatus.CANCELLED},
    JobStatus.EN_ROUTE: {JobStatus.ON_SITE, JobStatus.CANCELLED},
    JobStatus.ON_SITE: {JobStatus.DIAGNOSING, JobStatus.IN_PROGRESS, JobStatus.CANCELLED},
    JobStatus.DIAGNOSING: {JobStatus.AWAITING_APPROVAL, JobStatus.IN_PROGRESS, JobStatus.CANCELLED},
    JobStatus.AWAITING_APPROVAL: {JobStatus.IN_PROGRESS, JobStatus.CANCELLED},
    JobStatus.IN_PROGRESS: {JobStatus.COMPLETED, JobStatus.AWAITING_APPROVAL, JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),
    JobStatus.CANCELLED: set(),
}


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = JobRepository(session)

    async def transition(
        self,
        job_id: uuid.UUID,
        target: JobStatus,
        actor_id: uuid.UUID | None,
        actor_type: str,
        reason: str | None = None,
    ) -> Job:
        job = await self.repo.get(job_id, lock=True)
        if not job:
            raise HTTPException(404, "Job not found")
        if target == job.status:
            return job
        if target not in TRANSITIONS[job.status]:
            raise HTTPException(
                409, f"Cannot transition job from {job.status.value} to {target.value}"
            )
        previous = job.status
        job.status = target
        job.version += 1
        if target == JobStatus.COMPLETED:
            job.completed_at = datetime.now(UTC)
        self.repo.add_event(
            JobEvent(
                job_id=job.id,
                from_status=previous,
                to_status=target,
                actor_id=actor_id,
                actor_type=actor_type,
                reason=reason,
            )
        )
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def technician_note_transition(
        self,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        actor_id: uuid.UUID,
        notes_field: str,
        notes: str,
        target: JobStatus,
    ) -> Job:
        job = await self.repo.get(job_id, lock=True)
        if not job or job.worker_id != worker_id:
            raise HTTPException(403, "Technician is not assigned to this job")
        if target != job.status and target not in TRANSITIONS[job.status]:
            raise HTTPException(
                409, f"Cannot transition job from {job.status.value} to {target.value}"
            )
        previous = job.status
        setattr(job, notes_field, notes)
        if target != job.status:
            job.status = target
            job.version += 1
            if target == JobStatus.COMPLETED:
                job.completed_at = datetime.now(UTC)
            self.repo.add_event(
                JobEvent(
                    job_id=job.id,
                    from_status=previous,
                    to_status=target,
                    actor_id=actor_id,
                    actor_type="worker",
                    reason=f"{notes_field}_recorded",
                )
            )
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def create_work_request(
        self, job_id: uuid.UUID, payload: WorkRequestCreate, worker_id: uuid.UUID
    ) -> WorkRequest:
        job = await self.repo.get(job_id, lock=True)
        if not job:
            raise HTTPException(404, "Job not found")
        if job.worker_id != worker_id:
            raise HTTPException(403, "Worker is not assigned to this job")
        if job.status not in {JobStatus.ON_SITE, JobStatus.DIAGNOSING, JobStatus.IN_PROGRESS}:
            raise HTTPException(409, "Additional work cannot be requested in the current job state")
        items = [item.model_dump() for item in payload.line_items]
        subtotal = sum(item.quantity * item.unit_price_minor for item in payload.line_items)
        request = WorkRequest(
            job_id=job.id,
            status=WorkRequestStatus.SUBMITTED,
            description=payload.description,
            line_items=items,
            subtotal_minor=subtotal,
            tax_minor=payload.tax_minor,
            total_minor=subtotal + payload.tax_minor,
            currency=payload.currency,
            created_by=worker_id,
        )
        self.session.add(request)
        previous = job.status
        job.status = JobStatus.AWAITING_APPROVAL
        job.version += 1
        self.repo.add_event(
            JobEvent(
                job_id=job.id,
                from_status=previous,
                to_status=job.status,
                actor_id=worker_id,
                actor_type="worker",
                reason="additional_work_requested",
            )
        )
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def decide_work_request(
        self, request_id: uuid.UUID, approve: bool, customer_id: uuid.UUID
    ) -> WorkRequest:
        request = await self.repo.get_work_request(request_id, lock=True)
        if not request:
            raise HTTPException(404, "Work request not found")
        job = await self.repo.get(request.job_id, lock=True)
        if not job or job.customer_id != customer_id:
            raise HTTPException(403, "Not permitted to decide this request")
        if request.status != WorkRequestStatus.SUBMITTED:
            raise HTTPException(409, "Work request has already been decided")
        request.status = WorkRequestStatus.APPROVED if approve else WorkRequestStatus.DECLINED
        request.customer_decided_at = datetime.now(UTC)
        if not approve:
            previous = job.status
            job.status = JobStatus.IN_PROGRESS
            job.version += 1
            self.repo.add_event(
                JobEvent(
                    job_id=job.id,
                    from_status=previous,
                    to_status=job.status,
                    actor_id=customer_id,
                    actor_type="customer",
                    reason="additional_work_declined",
                )
            )
        await self.session.commit()
        await self.session.refresh(request)
        return request
