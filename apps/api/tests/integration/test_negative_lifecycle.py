import os
import uuid
from datetime import UTC, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from geoalchemy2.elements import WKTElement

from app.core.errors import DomainError
from app.db.session import SessionLocal, get_db
from app.domains.auth.dependencies import current_user
from app.domains.auth.models import User, UserRole
from app.domains.booking.models import Address, LegalEntity, ServiceArea
from app.domains.booking.schemas import (
    AddressValidateRequest,
    BookingCreateRequest,
    BookingWindow,
    CustomerInput,
)
from app.domains.booking.service import AddressService, BookingService
from app.domains.common.outbox import EventStatus, IntegrationEvent
from app.domains.common.outbox_service import OutboxService
from app.domains.dispatch.models import DispatchOffer, OfferStatus
from app.domains.dispatch.service import DispatchService
from app.domains.jobs.models import Job, JobStatus, WorkRequest, WorkRequestStatus
from app.domains.jobs.service import JobService
from app.integrations.geocoding import FakeGeocodingAdapter, GeocodedAddress
from app.main import app

postgres_only = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"), reason="requires PostgreSQL"
)


@postgres_only
@pytest.mark.asyncio
async def test_unserviceable_address_and_unavailable_slot() -> None:
    marker = uuid.uuid4().hex
    async with SessionLocal() as session:
        result = await AddressService(
            session,
            FakeGeocodingAdapter(
                GeocodedAddress("Nowhere", "Nowhere", "Ocean", "00000", "DE", 0, 0, "fake")
            ),
        ).validate(AddressValidateRequest(address="Nowhere in the ocean"))
        assert result.serviceable is False and result.address_id is None

        entity = LegalEntity(code=f"NEG-{marker[:8]}", name="Negative E2E", currency="EUR")
        session.add(entity)
        await session.flush()
        area = ServiceArea(
            legal_entity_id=entity.id,
            name="No availability",
            boundary=WKTElement(
                "MULTIPOLYGON(((30 30,31 30,31 31,30 31,30 30)))", srid=4326
            ),
            active=True,
        )
        session.add(area)
        await session.flush()
        address = Address(
            formatted_address="No Slot Street",
            line1="No Slot Street",
            city="Berlin",
            postal_code="10115",
            country_code="DE",
            location=WKTElement("POINT(30.5 30.5)", srid=4326),
            service_area_id=area.id,
            geocoding_provider="fake",
        )
        session.add(address)
        await session.commit()
        start = datetime.combine(
            (datetime.now(UTC) + timedelta(days=3)).date(), time(9), tzinfo=UTC
        )
        with pytest.raises(DomainError) as raised:
            await BookingService(session).create(
                BookingCreateRequest(
                    service_id=uuid.uuid4(),
                    customer=CustomerInput(
                        first_name="Negative",
                        last_name="Customer",
                        email=f"negative-{marker}@example.com",
                        phone="+49444444444",
                    ),
                    address_id=address.id,
                    window=BookingWindow(start=start, end=start + timedelta(hours=2)),
                ),
                f"unavailable-{marker}",
            )
        assert getattr(raised.value, "code", None) == "SLOT_UNAVAILABLE"


@postgres_only
@pytest.mark.asyncio
async def test_odoo_failure_dead_letters_then_authorized_retry_delivers() -> None:
    async with SessionLocal() as session:
        event = IntegrationEvent(
            aggregate_type="job",
            aggregate_id=uuid.uuid4(),
            event_type="job.completed",
            payload={"job_id": str(uuid.uuid4())},
            status=EventStatus.PENDING,
            attempts=4,
            available_at=datetime.now(UTC),
        )
        session.add(event)
        await session.commit()

        async def failed_odoo(_: IntegrationEvent) -> None:
            raise RuntimeError("fake Odoo unavailable")

        assert await OutboxService(session).process(failed_odoo, limit=1) == 1
        await session.refresh(event)
        assert event.status == EventStatus.DEAD_LETTER and event.attempt_count == 5
        await OutboxService(session).retry(event.id, uuid.uuid4())

        delivered: list[uuid.UUID] = []

        async def recovered_odoo(item: IntegrationEvent) -> None:
            delivered.append(item.id)

        assert await OutboxService(session).process(recovered_odoo, limit=1) == 1
        await session.refresh(event)
        assert event.status == EventStatus.DELIVERED and delivered == [event.id]


@pytest.mark.asyncio
async def test_wrong_customer_vendor_technician_and_invalid_transition_are_rejected() -> None:
    job_id, worker_id, customer_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    jobs = JobService(MagicMock())
    jobs.repo = AsyncMock()
    jobs.repo.get.return_value = Job(
        id=job_id,
        booking_id=uuid.uuid4(),
        customer_id=customer_id,
        service_id=uuid.uuid4(),
        address_id=uuid.uuid4(),
        worker_id=worker_id,
        status=JobStatus.ASSIGNED,
        scheduled_start=datetime.now(UTC),
        scheduled_end=datetime.now(UTC) + timedelta(hours=2),
        version=1,
    )
    with pytest.raises(HTTPException) as invalid:
        await jobs.transition(job_id, JobStatus.COMPLETED, uuid.uuid4(), "operations")
    assert invalid.value.status_code == 409

    with pytest.raises(HTTPException) as technician:
        await jobs.technician_note_transition(
            job_id,
            uuid.uuid4(),
            uuid.uuid4(),
            "diagnostic_notes",
            "wrong worker",
            JobStatus.EN_ROUTE,
        )
    assert technician.value.status_code == 403

    jobs.repo.get_work_request.return_value = WorkRequest(
        id=uuid.uuid4(),
        job_id=job_id,
        status=WorkRequestStatus.PENDING_CUSTOMER,
        description="quote",
        line_items=[],
        subtotal_minor=1,
        tax_minor=0,
        total_minor=1,
        currency="EUR",
        created_by=worker_id,
    )
    with pytest.raises(HTTPException) as customer:
        await jobs.decide_work_request(jobs.repo.get_work_request.return_value.id, True, uuid.uuid4())
    assert customer.value.status_code == 403

    dispatch = DispatchService(MagicMock())
    dispatch.repo = AsyncMock()
    dispatch.repo.get_offer.return_value = DispatchOffer(
        id=uuid.uuid4(),
        job_id=job_id,
        vendor_id=uuid.uuid4(),
        status=OfferStatus.PENDING,
        round=1,
        score=1,
        score_detail={},
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    with pytest.raises(HTTPException) as vendor:
        await dispatch.decide_offer(
            dispatch.repo.get_offer.return_value.id,
            uuid.uuid4(),
            True,
            worker_id,
            uuid.uuid4(),
        )
    assert vendor.value.status_code == 403


def test_dispatcher_cannot_approve_payout_or_read_arbitrary_payment() -> None:
    dispatcher = User(
        id=uuid.uuid4(),
        email="dispatcher@example.com",
        password_hash="unused",
        full_name="Dispatcher",
        role=UserRole.operations,
        is_active=True,
        email_verified=True,
        credential_version=1,
    )

    async def override_user() -> User:
        return dispatcher

    async def override_db():
        yield MagicMock()

    app.dependency_overrides[current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    try:
        client = TestClient(app)
        payout = client.post(f"/api/v1/finance/payout-batches/{uuid.uuid4()}/approve")
        assert payout.status_code == 403
        dispatcher.role = UserRole.customer
        payment = client.get(f"/api/v1/payments/{uuid.uuid4()}")
        assert payment.status_code == 403
    finally:
        app.dependency_overrides.clear()
