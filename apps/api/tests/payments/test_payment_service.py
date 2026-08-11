import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.domains.payments.exceptions import IdempotencyConflict, InvalidPaymentState
from app.domains.payments.models import IdempotencyRecord, Payment, PaymentStatus
from app.domains.payments.schemas import PaymentIntentCreate, ProviderIntent
from app.domains.payments.service import PaymentService


@pytest.fixture
def service() -> PaymentService:
    session = AsyncMock()
    provider = AsyncMock()
    result = PaymentService(session, provider)
    result.repo = AsyncMock()
    return result


@pytest.mark.asyncio
async def test_create_intent_persists_provider_result(service: PaymentService) -> None:
    booking_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    service.provider.create_intent.return_value = ProviderIntent(
        id="pi_123", status="requires_capture", client_secret="secret"
    )

    async def add(payment: Payment) -> Payment:
        payment.id = payment_id
        payment.created_at = payment.updated_at = datetime.now(UTC)
        return payment

    service.repo.add.side_effect = add
    service.repo.get_idempotency.return_value = None
    result = await service.create_intent(
        PaymentIntentCreate(booking_id=booking_id, amount_minor=12900), "request-key-123"
    )

    assert result.id == payment_id
    assert result.status == PaymentStatus.AUTHORIZED
    service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_idempotency_key_rejects_different_payload(service: PaymentService) -> None:
    service.repo.get_idempotency.return_value = IdempotencyRecord(
        operation="create_intent", idempotency_key="request-key-123",
        request_hash="different",
    )
    with pytest.raises(IdempotencyConflict):
        await service.create_intent(
            PaymentIntentCreate(booking_id=uuid.uuid4(), amount_minor=1000), "request-key-123"
        )


@pytest.mark.asyncio
async def test_capture_requires_authorization(service: PaymentService) -> None:
    service.repo.get.return_value = Payment(
        id=uuid.uuid4(), booking_id=uuid.uuid4(), amount_minor=1000, currency="usd",
        status=PaymentStatus.CREATED,
    )
    with pytest.raises(InvalidPaymentState):
        await service.capture(service.repo.get.return_value.id, None, "capture-key-123")


@pytest.mark.asyncio
async def test_duplicate_webhook_is_noop(service: PaymentService) -> None:
    service.provider.verify_webhook.return_value = {
        "id": "evt_123", "type": "payment_intent.succeeded", "data": {"object": {}}
    }
    service.repo.event_exists.return_value = True

    assert await service.process_webhook(b"{}", "signature") == ("evt_123", True)
    service.repo.add_event.assert_not_awaited()
    service.session.commit.assert_not_awaited()
