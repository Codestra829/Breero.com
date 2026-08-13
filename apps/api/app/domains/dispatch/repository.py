import uuid
from datetime import date, datetime
from typing import cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workforce.models import Vendor, VendorStatus, Worker, WorkerStatus

from .models import DispatchOffer, OfferStatus


class DispatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def candidate_workers(
        self, capabilities: list[str], postal_code: str, on_date: date, limit=20
    ):
        query = (
            select(Vendor, Worker)
            .join(Worker, Worker.vendor_id == Vendor.id)
            .where(Vendor.status == VendorStatus.ACTIVE)
            .where(Worker.status == WorkerStatus.ACTIVE, Worker.available.is_(True))
            .where(Vendor.covered_postal_codes.contains([postal_code]))
            .where(Vendor.license_valid_until >= on_date)
            .where(Vendor.insurance_valid_until >= on_date)
            .limit(limit)
        )
        if capabilities:
            query = query.where(Vendor.capabilities.contains(capabilities))
        return list((await self.session.execute(query)).all())

    async def get_offer(self, offer_id: uuid.UUID, lock=False) -> DispatchOffer | None:
        query = select(DispatchOffer).where(DispatchOffer.id == offer_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def offers_for_job(self, job_id: uuid.UUID) -> list[DispatchOffer]:
        return list(
            (
                await self.session.scalars(
                    select(DispatchOffer)
                    .where(DispatchOffer.job_id == job_id)
                    .order_by(DispatchOffer.score.desc())
                )
            ).all()
        )

    async def expire_due(self, now: datetime) -> int:
        result = await self.session.execute(
            update(DispatchOffer)
            .where(DispatchOffer.status == OfferStatus.PENDING, DispatchOffer.expires_at <= now)
            .values(status=OfferStatus.EXPIRED)
        )
        return cast(CursorResult, result).rowcount or 0
