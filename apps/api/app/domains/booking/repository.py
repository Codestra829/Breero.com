import uuid
from datetime import datetime

from geoalchemy2.functions import ST_Covers
from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.booking.models import (
    Address,
    AvailabilityRule,
    Booking,
    Customer,
    LegalEntity,
    ServiceArea,
)


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def service_area_at(
        self, longitude: float, latitude: float
    ) -> tuple[ServiceArea, LegalEntity] | None:
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
        stmt = (
            select(ServiceArea, LegalEntity)
            .join(LegalEntity, LegalEntity.id == ServiceArea.legal_entity_id)
            .where(
                ServiceArea.active.is_(True),
                LegalEntity.active.is_(True),
                ST_Covers(ServiceArea.boundary, point),
            )
            .limit(1)
        )
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    async def add_address(self, address: Address) -> Address:
        self.session.add(address)
        await self.session.flush()
        return address

    async def address(self, address_id: uuid.UUID) -> Address | None:
        return await self.session.get(Address, address_id)

    async def legal_entity_for_area(self, area_id: uuid.UUID) -> LegalEntity | None:
        stmt = select(LegalEntity).join(ServiceArea).where(ServiceArea.id == area_id)
        return await self.session.scalar(stmt)

    async def availability_rules(
        self, service_id: uuid.UUID, area_id: uuid.UUID
    ) -> list[AvailabilityRule]:
        stmt = select(AvailabilityRule).where(
            AvailabilityRule.service_id == service_id,
            AvailabilityRule.service_area_id == area_id,
        )
        return list((await self.session.scalars(stmt)).all())

    async def booking_count(self, service_id: uuid.UUID, start: datetime, end: datetime) -> int:
        stmt = select(func.count(Booking.id)).where(
            Booking.service_id == service_id,
            Booking.window_start == start,
            Booking.window_end == end,
            Booking.status.in_(["PENDING_PAYMENT", "CONFIRMED"]),
        )
        return int(await self.session.scalar(stmt) or 0)

    async def lock_slot(self, service_id: uuid.UUID, start: datetime, end: datetime) -> None:
        """Serialize capacity decisions for one service/window across API processes."""
        key = f"booking-slot:{service_id}:{start.isoformat()}:{end.isoformat()}"
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key}
        )

    async def lock_idempotency_key(self, key: str) -> None:
        """Serialize lookup/create for one booking idempotency key across API processes."""
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"booking-idempotency:{key}"},
        )

    async def booking_by_idempotency_key(self, key: str) -> Booking | None:
        return await self.session.scalar(select(Booking).where(Booking.idempotency_key == key))

    async def customer_for_email(self, email: str) -> Customer | None:
        return await self.session.scalar(select(Customer).where(Customer.email == email).limit(1))

    async def add(self, instance: object) -> None:
        self.session.add(instance)
        await self.session.flush()

    async def customer_bookings(self, customer_id: uuid.UUID) -> list[Booking]:
        stmt: Select[tuple[Booking]] = (
            select(Booking)
            .where(Booking.customer_id == customer_id)
            .order_by(Booking.created_at.desc())
        )
        return list((await self.session.scalars(stmt)).all())
