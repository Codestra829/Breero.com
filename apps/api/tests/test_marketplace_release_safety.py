import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.errors import DomainError
from app.domains.booking.models import (
    CAPACITY_HOLDING_STATUSES,
    EXPIRING_BOOKING_STATUSES,
    BookingStatus,
)
from app.domains.booking.repository import BookingRepository
from app.domains.booking.schemas import (
    BookingCreateRequest,
    BookingWindow,
    CustomerInput,
)
from app.domains.booking.service import BookingService
from app.domains.capabilities.service import public_capabilities
from app.domains.common.outbox import EventStatus, IntegrationEvent
from app.domains.common.outbox_service import INTEGRATION_DISABLED_ERROR_CODE, OutboxService
from app.main import app


def test_public_capabilities_report_effective_request_only_runtime() -> None:
    response = TestClient(app).get("/api/v1/public/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "request_intake": True,
        "instant_booking": False,
        "online_payments": False,
        "automatic_assignment": False,
        "provider_self_service": False,
        "marketplace_matching": False,
        "messaging": False,
        "reviews": False,
    }


def test_capabilities_require_complete_effective_flag_sets() -> None:
    partial = Settings(
        payments_enabled=True,
        stripe_enabled=True,
        online_checkout_enabled=False,
        automatic_booking_enabled=True,
        automatic_confirmed_bookings=False,
    )
    assert public_capabilities(partial).online_payments is False
    assert public_capabilities(partial).instant_booking is False
    assert public_capabilities(
        Settings(scheduling_enabled=False, automatic_provider_assignment_enabled=True)
    ).automatic_assignment is False


@pytest.mark.asyncio
async def test_non_bookable_service_cannot_use_booking_command(monkeypatch) -> None:
    start = datetime.now(UTC) + timedelta(days=2)
    payload = BookingCreateRequest(
        service_id=uuid.uuid4(),
        address_id=uuid.uuid4(),
        customer=CustomerInput(
            first_name="Release", last_name="Safety", email="safety@example.com", phone="+12815550100"
        ),
        window=BookingWindow(start=start, end=start + timedelta(hours=1)),
        answers=[],
    )
    service = BookingService(MagicMock())
    service.repository = AsyncMock()
    service.repository.booking_by_idempotency_key.return_value = None
    service.repository.address.return_value = SimpleNamespace(
        id=payload.address_id, service_area_id=uuid.uuid4(), timezone_name="UTC", postal_code="77433"
    )
    service.repository.eligible_provider_hours.return_value = [(SimpleNamespace(), SimpleNamespace())]
    service.repository.legal_entity_for_area.return_value = SimpleNamespace(id=uuid.uuid4(), currency="USD")
    service.availability = AsyncMock()
    service.availability.search.return_value = [
        SimpleNamespace(start=payload.window.start, end=payload.window.end)
    ]
    catalog = AsyncMock()
    catalog.active_detail.return_value = SimpleNamespace(
        id=payload.service_id, name="Request only", is_bookable=False, questions=[]
    )
    monkeypatch.setattr("app.domains.booking.service.CatalogRepository", lambda _: catalog)

    with pytest.raises(DomainError) as raised:
        await service.create(payload, "release-safety-booking-key")

    assert raised.value.code == "SERVICE_NOT_BOOKABLE"
    service.repository.address.assert_not_awaited()


def test_expiry_worker_covers_every_capacity_holding_status() -> None:
    assert CAPACITY_HOLDING_STATUSES.issubset(EXPIRING_BOOKING_STATUSES)


@pytest.mark.asyncio
async def test_capacity_queries_exclude_expired_non_confirmed_holds() -> None:
    session = AsyncMock()
    session.scalar.return_value = 0
    repository = BookingRepository(session)
    now = datetime.now(UTC) + timedelta(days=1)

    await repository.booking_count(uuid.uuid4(), now, now + timedelta(hours=1))
    booking_statement = session.scalar.await_args.args[0]
    booking_sql = str(booking_statement)
    await repository.provider_booking_count(uuid.uuid4(), now, now + timedelta(hours=1))
    provider_sql = str(session.scalar.await_args.args[0])

    assert "bookings.expires_at" in booking_sql
    assert "bookings.expires_at" in provider_sql
    assert BookingStatus.CONFIRMED in booking_statement.compile().params.values()


@pytest.mark.asyncio
async def test_disabled_middleware_parks_public_submission_events() -> None:
    event = IntegrationEvent(
        aggregate_type="public_submission",
        aggregate_id=uuid.uuid4(),
        event_type="breero.service_request.created",
        aggregate_version=1,
        schema_version=1,
        idempotency_key=f"release-safety:{uuid.uuid4()}",
        payload={},
        status=EventStatus.PENDING,
        next_attempt_at=datetime.now(UTC),
    )
    scalars = MagicMock()
    scalars.all.return_value = [event]
    session = AsyncMock()
    session.scalars.return_value = scalars

    outbox = OutboxService(session)
    assert await outbox.park_unconfigured() == 1
    assert event.status == EventStatus.PENDING_CONFIGURATION
    assert event.processed_at is None
    assert event.last_error_code == INTEGRATION_DISABLED_ERROR_CODE
    assert event.last_error == "Integration disabled or unconfigured"
    assert event.last_error_at is not None

    assert await outbox.activate_pending_configuration() == 1
    assert event.status == EventStatus.PENDING
    assert event.last_error_code is None
    assert event.last_error is None
    assert event.last_error_at is None
    assert session.commit.await_count == 2
