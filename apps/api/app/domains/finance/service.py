import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.jobs.models import Job, JobStatus

from .models import EarningStatus, PayoutBatch, PayoutStatus, VendorEarning
from .repository import FinanceRepository


class FinanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FinanceRepository(session)

    async def recognize_earning(
        self, job: Job, gross_minor: int, fee_minor: int, currency: str = "USD"
    ) -> VendorEarning:
        if job.status != JobStatus.COMPLETED or not job.vendor_id:
            raise HTTPException(409, "Only completed assigned jobs can create earnings")
        if gross_minor < 0 or fee_minor < 0 or fee_minor > gross_minor:
            raise HTTPException(422, "Invalid earning amounts")
        existing = await self.repo.earning_for_job(job.id)
        if existing:
            return existing
        earning = VendorEarning(
            vendor_id=job.vendor_id,
            job_id=job.id,
            gross_minor=gross_minor,
            fee_minor=fee_minor,
            net_minor=gross_minor - fee_minor,
            currency=currency,
            status=EarningStatus.PENDING,
            available_at=datetime.now(UTC) + timedelta(days=7),
        )
        self.session.add(earning)
        await self.session.commit()
        await self.session.refresh(earning)
        return earning

    async def create_batch(self, currency: str, vendor_id=None) -> PayoutBatch:
        earnings = await self.repo.available_earnings(currency, vendor_id, lock=True)
        if not earnings:
            raise HTTPException(409, "No available earnings")
        batch = PayoutBatch(
            reference=f"PAY-{datetime.now(UTC):%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
            status=PayoutStatus.PENDING_APPROVAL,
            currency=currency,
            total_minor=sum(e.net_minor for e in earnings),
            earning_count=len(earnings),
        )
        self.session.add(batch)
        await self.session.flush()
        for earning in earnings:
            earning.status = EarningStatus.BATCHED
            earning.payout_batch_id = batch.id
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def approve_batch(self, batch_id: uuid.UUID, approver_id: uuid.UUID) -> PayoutBatch:
        batch = await self.repo.get_batch(batch_id, lock=True)
        if not batch:
            raise HTTPException(404, "Payout batch not found")
        if batch.status != PayoutStatus.PENDING_APPROVAL:
            raise HTTPException(409, "Batch is not awaiting approval")
        batch.status = PayoutStatus.APPROVED
        batch.approved_by = approver_id
        batch.approved_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def mark_processing(self, batch_id: uuid.UUID) -> PayoutBatch:
        batch = await self.repo.get_batch(batch_id, lock=True)
        if not batch:
            raise HTTPException(404, "Payout batch not found")
        if batch.status != PayoutStatus.APPROVED:
            raise HTTPException(409, "Only approved batches can be processed")
        batch.status = PayoutStatus.PROCESSING
        await self.session.commit()
        return batch
