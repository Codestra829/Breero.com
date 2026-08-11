import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import EarningStatus, PayoutBatch, VendorEarning


class FinanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_earnings(self, vendor_id=None, status=None, limit=200):
        query = (
            select(VendorEarning).order_by(VendorEarning.created_at.desc()).limit(min(limit, 500))
        )
        if vendor_id:
            query = query.where(VendorEarning.vendor_id == vendor_id)
        if status:
            query = query.where(VendorEarning.status == status)
        return list((await self.session.scalars(query)).all())

    async def earning_for_job(self, job_id: uuid.UUID) -> VendorEarning | None:
        return await self.session.scalar(
            select(VendorEarning).where(VendorEarning.job_id == job_id)
        )

    async def available_earnings(self, currency, vendor_id=None, lock=False):
        query = (
            select(VendorEarning)
            .where(
                VendorEarning.status == EarningStatus.AVAILABLE,
                VendorEarning.currency == currency,
            )
            .order_by(VendorEarning.available_at)
        )
        if vendor_id:
            query = query.where(VendorEarning.vendor_id == vendor_id)
        if lock:
            query = query.with_for_update(skip_locked=True)
        return list((await self.session.scalars(query)).all())

    async def get_batch(self, batch_id: uuid.UUID, lock=False) -> PayoutBatch | None:
        query = select(PayoutBatch).where(PayoutBatch.id == batch_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)
