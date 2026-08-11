import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.booking.models import Booking, BookingStatus
from app.domains.jobs.models import WorkRequest, WorkRequestStatus
from app.domains.payments.exceptions import IdempotencyConflict, InvalidPaymentState
from app.domains.payments.models import (
    IdempotencyRecord,
    Payment,
    PaymentEvent,
    PaymentPurpose,
    PaymentStatus,
    RefundStatus,
)
from app.domains.payments.schemas import PaymentIntentCreate, ProviderIntent, ProviderRefund
from app.domains.payments.service import PaymentService


@pytest.fixture
def service() -> PaymentService:
    session = AsyncMock()
    session.add = MagicMock()
    provider = MagicMock()
    provider.create_intent = AsyncMock()
    provider.capture_intent = AsyncMock()
    result = PaymentService(session, provider)
    result.repo = AsyncMock()
    result.repo.get_event.return_value = None
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
    service.session.scalar.return_value = Booking(
        id=booking_id,
        total_amount=129,
        currency="USD",
        status=BookingStatus.PENDING_PAYMENT,
    )
    result = await service.create_intent(
        PaymentIntentCreate(booking_id=booking_id, amount_minor=12900), "request-key-123"
    )

    assert result.id == payment_id
    assert result.status == PaymentStatus.AUTHORIZED
    service.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_idempotency_key_rejects_different_payload(service: PaymentService) -> None:
    service.repo.get_idempotency.return_value = IdempotencyRecord(
        operation="create_intent",
        idempotency_key="request-key-123",
        request_hash="different",
    )
    with pytest.raises(IdempotencyConflict):
        await service.create_intent(
            PaymentIntentCreate(booking_id=uuid.uuid4(), amount_minor=1000), "request-key-123"
        )


@pytest.mark.asyncio
async def test_capture_requires_authorization(service: PaymentService) -> None:
    service.repo.get.return_value = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        amount_minor=1000,
        currency="usd",
        status=PaymentStatus.CREATED,
    )
    with pytest.raises(InvalidPaymentState):
        await service.capture(service.repo.get.return_value.id, None, "capture-key-123")


@pytest.mark.asyncio
async def test_duplicate_webhook_is_noop(service: PaymentService) -> None:
    service.provider.verify_webhook.return_value = {
        "id": "evt_123",
        "type": "payment_intent.succeeded",
        "data": {"object": {}},
    }
    service.repo.get_event.return_value = PaymentEvent(
        provider="stripe",
        provider_event_id="evt_123",
        event_type="payment_intent.succeeded",
        payload={},
        status="processed",
    )

    assert await service.process_webhook(b"{}", "signature") == ("evt_123", True)
    service.repo.add_event.assert_not_awaited()
    service.session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_quote_intent_requires_customer_approval(service: PaymentService) -> None:
    quote_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    service.repo.get_idempotency.return_value = None
    service.provider.create_intent.return_value = ProviderIntent(
        id="pi_quote", status="requires_action", client_secret="secret"
    )
    service.session.scalar.return_value = WorkRequest(
        id=quote_id,
        job_id=uuid.uuid4(),
        status=WorkRequestStatus.APPROVED_PENDING_PAYMENT,
        total_minor=2050,
        currency="USD",
    )

    async def add(payment: Payment) -> Payment:
        payment.id = payment_id
        payment.created_at = payment.updated_at = datetime.now(UTC)
        return payment

    service.repo.add.side_effect = add
    result = await service.create_intent(
        PaymentIntentCreate(
            quote_id=quote_id,
            payment_purpose=PaymentPurpose.QUOTE_ADDITIONAL_WORK,
            amount_minor=2050,
            currency="usd",
        ),
        "quote-payment-key",
    )
    assert result.payment_purpose == PaymentPurpose.QUOTE_ADDITIONAL_WORK
    assert result.quote_id == quote_id


@pytest.mark.asyncio
async def test_partial_refund_updates_payment(service: PaymentService) -> None:
    payment = Payment(
        id=uuid.uuid4(),
        booking_id=uuid.uuid4(),
        provider_payment_id="pi_123",
        payment_purpose=PaymentPurpose.BOOKING_DIAGNOSTIC,
        amount_minor=1000,
        captured_amount_minor=1000,
        currency="usd",
        status=PaymentStatus.CAPTURED,
    )
    service.repo.get.return_value = payment
    service.repo.refund_by_key.return_value = None
    service.session.scalar.return_value = 0
    service.provider.create_refund = AsyncMock(
        return_value=ProviderRefund(id="re_123", status="succeeded")
    )

    async def refresh(refund) -> None:
        refund.id = uuid.uuid4()
        refund.created_at = datetime.now(UTC)

    service.session.refresh.side_effect = refresh
    result = await service.refund(payment.id, 400, "refund-key-123", uuid.uuid4(), None)
    assert result.amount_minor == 400
    assert result.status == RefundStatus.SUCCEEDED
    assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
