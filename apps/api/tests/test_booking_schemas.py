import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domains.booking.schemas import (
    AddressValidateRequest,
    AvailabilitySearchRequest,
    BookingCreateRequest,
)


def test_address_coordinates_must_be_supplied_as_pair() -> None:
    with pytest.raises(ValidationError):
        AddressValidateRequest(address="Alexanderplatz, Berlin", latitude=52.52)


def test_availability_rejects_reverse_or_excessive_range() -> None:
    with pytest.raises(ValidationError):
        AvailabilitySearchRequest(
            service_id=uuid.uuid4(),
            address_id=uuid.uuid4(),
            date_from=date(2026, 2, 2),
            date_to=date(2026, 2, 1),
        )
    with pytest.raises(ValidationError):
        AvailabilitySearchRequest(
            service_id=uuid.uuid4(),
            address_id=uuid.uuid4(),
            date_from=date(2026, 1, 1),
            date_to=date(2026, 3, 1),
        )


def test_booking_answers_default_is_not_shared() -> None:
    now = datetime.now(UTC) + timedelta(days=1)
    common = {
        "service_id": uuid.uuid4(),
        "address_id": uuid.uuid4(),
        "customer": {
            "first_name": "A",
            "last_name": "B",
            "email": "a@example.com",
            "phone": "+49123456",
        },
        "window": {"start": now, "end": now + timedelta(hours=2)},
    }
    first = BookingCreateRequest(**common)
    second = BookingCreateRequest(**common)
    assert first.answers == second.answers == []
    assert first.answers is not second.answers
