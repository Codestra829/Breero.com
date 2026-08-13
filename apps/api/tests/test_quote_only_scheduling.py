from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.domains.booking.models import BookingStatus
from app.domains.dispatch.service import DispatchService
from app.domains.public_submissions.schemas import ServiceRequestCreate
from app.main import app


def production_settings(**overrides) -> dict:
    values = {
        "app_env": "production",
        "database_url": "postgresql+psycopg://service:nondefault@db:5432/breero",
        "redis_url": "redis://:nondefault@redis:6379/0",
        "jwt_secret": "a" * 32,
        "jwt_refresh_secret": "b" * 32,
        "cors_origins": "https://breero.com",
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    "flag",
    ["stripe_enabled", "payout_enabled", "paid_leads_enabled"],
)
def test_production_payment_flags_fail_closed(flag: str) -> None:
    with pytest.raises(ValidationError, match="quote-only"):
        Settings(**production_settings(**{flag: True}))


@pytest.mark.parametrize(
    "flag",
    ["automatic_booking_enabled", "automatic_provider_assignment_enabled"],
)
def test_automatic_scheduling_flags_fail_closed(flag: str) -> None:
    with pytest.raises(ValidationError, match="automatic booking"):
        Settings(**production_settings(**{flag: True}))


def test_quote_only_booking_states_do_not_imply_confirmation() -> None:
    assert BookingStatus.REQUESTED.value == "REQUESTED"
    assert BookingStatus.PENDING_MANUAL_DISPATCH.value == "PENDING_MANUAL_DISPATCH"
    assert BookingStatus.TENTATIVE_HOLD.value == "TENTATIVE_HOLD"
    assert BookingStatus.SCHEDULED.value == "SCHEDULED"
    assert BookingStatus.REQUESTED is not BookingStatus.CONFIRMED


def test_provider_working_hours_use_service_local_time() -> None:
    hours = {"0": [["07:00", "19:00"]]}
    assert DispatchService._supports_working_hours(
        hours,
        datetime(2026, 8, 17, 7, 0, tzinfo=UTC),
        datetime(2026, 8, 17, 9, 0, tzinfo=UTC),
    )
    assert not DispatchService._supports_working_hours(
        hours,
        datetime(2026, 8, 17, 18, 0, tzinfo=UTC),
        datetime(2026, 8, 17, 20, 0, tzinfo=UTC),
    )
    assert not DispatchService._supports_working_hours(
        {},
        datetime(2026, 8, 17, 7, 0, tzinfo=UTC),
        datetime(2026, 8, 17, 9, 0, tzinfo=UTC),
    )


def test_payment_routes_are_absent_when_disabled() -> None:
    response = TestClient(app).post("/api/v1/payments/intents", json={})
    assert response.status_code == 404


@pytest.mark.parametrize("state", ["AL", "CA", "NY", "TX", "DC", "WY"])
def test_nationwide_request_intake_accepts_us_states_and_dc(state: str) -> None:
    request = ServiceRequestCreate(
        source_url="https://breero.com/booking",
        name="Synthetic Customer",
        email="synthetic@example.com",
        phone="+12025550100",
        service_slug="home-cleaning",
        service_description="Synthetic request for validation only",
        address_line1="100 Test Street",
        city="Test City",
        state=state,
        postal_code="20001",
        contact_preference="email",
    )
    assert request.state == state


def test_request_intake_rejects_non_us_region() -> None:
    with pytest.raises(ValidationError, match="valid U.S. state"):
        ServiceRequestCreate(
            source_url="https://breero.com/booking",
            name="Synthetic Customer",
            email="synthetic@example.com",
            phone="+12025550100",
            service_slug="home-cleaning",
            service_description="Synthetic request for validation only",
            address_line1="100 Test Street",
            city="Test City",
            state="ZZ",
            postal_code="20001",
            contact_preference="email",
        )
