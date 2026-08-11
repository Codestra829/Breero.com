from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Job, JobEvent, WorkRequest


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, job_id: uuid.UUID, *, lock: bool = False) -> Job | None:
        query = select(Job).where(Job.id == job_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def list(self, *, status=None, vendor_id=None, worker_id=None, limit=100) -> list[Job]:
        query = select(Job).order_by(Job.scheduled_start).limit(min(limit, 200))
        if status:
            query = query.where(Job.status == status)
        if vendor_id:
            query = query.where(Job.vendor_id == vendor_id)
        if worker_id:
            query = query.where(Job.worker_id == worker_id)
        return list((await self.session.scalars(query)).all())

    def add_event(self, event: JobEvent) -> None:
        self.session.add(event)

    async def get_work_request(self, request_id: uuid.UUID, *, lock=False) -> WorkRequest | None:
        query = select(WorkRequest).where(WorkRequest.id == request_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def list_work_requests(self, job_id: uuid.UUID) -> list[WorkRequest]:
        result = await self.session.scalars(
            select(WorkRequest).where(WorkRequest.job_id == job_id).order_by(WorkRequest.created_at)
        )
        return list(result.all())
