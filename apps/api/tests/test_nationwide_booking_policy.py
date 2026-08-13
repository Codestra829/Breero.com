from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.domains.booking.service import evaluation_fee
from app.domains.public_submissions.schemas import ServiceRequestCreate
from app.domains.workforce.schemas import BookingCoverageWrite


def test_regular_and_sunday_evaluation_fees_use_service_address_day() -> None:
    zone = ZoneInfo("America/New_York")
    assert evaluation_fee(datetime(2026, 8, 15, 7, tzinfo=zone)) == Decimal("200.00")
    assert evaluation_fee(datetime(2026, 8, 16, 7, tzinfo=zone)) == Decimal("300.00")


def test_provider_coverage_enforces_fixed_hours_and_capacity() -> None:
    valid = BookingCoverageWrite(
        service_ids=["00000000-0000-0000-0000-000000000001"],
        postal_codes=["78701"],
    )
    assert valid.start_time == time(7) and valid.end_time == time(19) and valid.capacity == 1
    with pytest.raises(ValidationError):
        BookingCoverageWrite(
            service_ids=["00000000-0000-0000-0000-000000000001"],
            postal_codes=["78701"], capacity=2,
        )


def test_manual_dispatch_requests_accept_all_us_states_and_dc() -> None:
    common = {
        "name": "Test Customer", "email": "customer@example.com", "phone": "+15125550123",
        "service_slug": "plumbing", "service_description": "Leaking kitchen fixture",
        "address_line1": "1 Main St", "city": "Washington", "postal_code": "20001",
        "contact_preference": "email", "source_url": "https://breero.com/request-service",
    }
    assert ServiceRequestCreate(**common, state="DC").state == "DC"
    assert ServiceRequestCreate(**common, state="CA").state == "CA"
    with pytest.raises(ValidationError):
        ServiceRequestCreate(**common, state="PR")
