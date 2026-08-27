import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.errors import DomainError
from app.db.session import SessionLocal
from app.domains.booking_intents.models import BookingIntent, BookingIntentStatus
from app.domains.booking_intents.schemas import BookingIntentCreate, BookingIntentUpdate
from app.domains.booking_intents.service import BookingIntentService
from app.domains.catalog.models import Service
from app.domains.common.outbox import AuditLog

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="booking-intent integration requires PostgreSQL",
)


@pytest.mark.asyncio
async def test_booking_intent_persists_is_session_scoped_and_uses_versions() -> None:
    marker = uuid.uuid4().hex
    owner_session = uuid.uuid4()
    other_session = uuid.uuid4()

    async with SessionLocal() as session:
        catalog_service = Service(
            slug=f"intent-service-{marker}",
            name="Intent service",
            description="Booking intent integration fixture",
            category="test",
            pricing_model="request_only",
            duration_minutes=60,
            is_active=True,
            is_bookable=False,
        )
        session.add(catalog_service)
        await session.commit()
        await session.refresh(catalog_service)

        service = BookingIntentService(session)
        intent = await service.create(
            BookingIntentCreate(service_id=catalog_service.id),
            owner_session,
        )
        assert intent.status == BookingIntentStatus.DRAFT
        assert intent.version == 1
        assert intent.expires_at > datetime.now(UTC) + timedelta(minutes=110)

        persisted = await session.scalar(
            select(BookingIntent).where(BookingIntent.id == intent.id)
        )
        assert persisted and persisted.anonymous_session_id == owner_session

        with pytest.raises(DomainError) as invisible:
            await service.get(intent.id, other_session)
        assert invisible.value.status_code == 404

        requested_date = datetime.now(UTC).date() + timedelta(days=2)
        updated = await service.update(
            intent.id,
            owner_session,
            BookingIntentUpdate(
                timezone_id="America/Chicago",
                requested_date=requested_date,
            ),
            expected_version=1,
        )
        assert updated.timezone_id == "America/Chicago"
        assert updated.requested_date == requested_date
        assert updated.version == 2

        with pytest.raises(DomainError) as conflict:
            await service.update(
                intent.id,
                owner_session,
                BookingIntentUpdate(requested_date=requested_date + timedelta(days=1)),
                expected_version=1,
            )
        assert conflict.value.code == "BOOKING_INTENT_VERSION_CONFLICT"

        await service.abandon(
            intent.id,
            owner_session,
            expected_version=2,
        )
        await session.refresh(intent)
        assert intent.status == BookingIntentStatus.EXPIRED
        assert intent.version == 3

        actions = set(
            (
                await session.scalars(
                    select(AuditLog.action).where(AuditLog.resource_id == intent.id)
                )
            ).all()
        )
        assert {
            "booking_intent.create",
            "booking_intent.update",
            "booking_intent.abandon",
        } <= actions
