import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from geoalchemy2.elements import WKTElement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Vendor, VendorStatus, Worker, WorkerLocationEvent, WorkerStatus
from .repository import WorkforceRepository
from .schemas import LocationUpdate, VendorCreate, WorkerCreate


class WorkforceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WorkforceRepository(session)

    async def create_vendor(self, payload: VendorCreate) -> Vendor:
        location = None
        if payload.latitude is not None and payload.longitude is not None:
            location = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
        vendor = Vendor(
            **payload.model_dump(exclude={"latitude", "longitude"}),
            status=VendorStatus.PENDING,
            home_location=location,
        )
        self.session.add(vendor)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(409, "Vendor email already exists") from exc
        await self.session.refresh(vendor)
        return vendor

    async def add_worker(self, vendor_id: uuid.UUID, payload: WorkerCreate) -> Worker:
        vendor = await self.repo.get_vendor(vendor_id)
        if not vendor:
            raise HTTPException(404, "Vendor not found")
        worker = Worker(vendor_id=vendor_id, status=WorkerStatus.INVITED, **payload.model_dump())
        self.session.add(worker)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise HTTPException(409, "Worker already exists") from exc
        await self.session.refresh(worker)
        return worker

    async def record_location(
        self, worker_id: uuid.UUID, payload: LocationUpdate, authenticated_worker_id: uuid.UUID
    ) -> Worker:
        if worker_id != authenticated_worker_id:
            raise HTTPException(403, "Workers may only update their own location")
        worker = await self.repo.get_worker(worker_id)
        if not worker or worker.status != WorkerStatus.ACTIVE:
            raise HTTPException(404, "Active worker not found")
        point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
        worker.current_location = point
        worker.location_updated_at = datetime.now(UTC)
        self.session.add(
            WorkerLocationEvent(
                worker_id=worker.id, location=point, accuracy_meters=payload.accuracy_meters
            )
        )
        await self.session.commit()
        await self.session.refresh(worker)
        return worker
