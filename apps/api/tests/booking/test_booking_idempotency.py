from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.errors import DomainError
from app.domains.booking.schemas import BookingCreateRequest, BookingWindow, CustomerInput
from app.domains.booking.service import BookingService


def request(email: str = "guest@example.com") -> BookingCreateRequest:
    start = datetime.now(UTC) + timedelta(days=2)
    return BookingCreateRequest(
        service_id=uuid4(),
        customer=CustomerInput(
            first_name="Guest", last_name="Customer", email=email, phone="+49123456789"
        ),
        address_id=uuid4(),
        window=BookingWindow(start=start, end=start + timedelta(hours=2)),
    )


@pytest.mark.asyncio
async def test_reused_booking_key_rejects_different_intent() -> None:
    service = BookingService(MagicMock())
    service.repository.booking_by_idempotency_key = AsyncMock(
        return_value=SimpleNamespace(idempotency_request_hash="0" * 64)
    )

    with pytest.raises(DomainError) as raised:
        await service.create(request(), "same-booking-key")

    assert raised.value.code == "IDEMPOTENCY_CONFLICT"
    assert raised.value.status_code == 409
