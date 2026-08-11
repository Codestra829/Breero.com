import hashlib
import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.stripe import PaymentProvider

from .exceptions import IdempotencyConflict, InvalidPaymentState, PaymentNotFound
from .models import IdempotencyRecord, Payment, PaymentStatus
from .repository import PaymentRepository
from .schemas import PaymentIntentCreate, PaymentView

STRIPE_STATUS = {
    "requires_payment_method": PaymentStatus.CREATED,
    "requires_confirmation": PaymentStatus.CREATED,
    "requires_action": PaymentStatus.REQUIRES_ACTION,
    "processing": PaymentStatus.AUTHORIZED,
    "requires_capture": PaymentStatus.AUTHORIZED,
    "succeeded": PaymentStatus.CAPTURED,
    "canceled": PaymentStatus.CANCELED,
}


class PaymentService:
    def __init__(self, session: AsyncSession, provider: PaymentProvider) -> None:
        self.session = session
        self.repo = PaymentRepository(session)
        self.provider = provider

    async def create_intent(self, payload: PaymentIntentCreate, key: str) -> PaymentView:
        request = payload.model_dump(mode="json")
        request_hash = self._hash(request)
        await self.repo.lock_key("create_intent", key)
        existing = await self.repo.get_idempotency("create_intent", key)
        if existing:
            if existing.request_hash != request_hash:
                raise IdempotencyConflict("Idempotency key was already used with another request")
            if not existing.response_body:
                raise IdempotencyConflict("Request with this idempotency key is still processing")
            payment = await self.repo.get(uuid.UUID(existing.response_body["id"]))
            if payment is None:
                raise PaymentNotFound("Stored idempotent payment no longer exists")
            return self._view(payment)

        record = IdempotencyRecord(
            operation="create_intent", idempotency_key=key, request_hash=request_hash
        )
        await self.repo.add_idempotency(record)
        provider_intent = await self.provider.create_intent(
            amount_minor=payload.amount_minor, currency=payload.currency,
            capture_method=payload.capture_method,
            metadata={**payload.metadata, "booking_id": str(payload.booking_id)},
            idempotency_key=key,
        )
        payment = await self.repo.add(Payment(
            booking_id=payload.booking_id, provider_payment_id=provider_intent.id,
            status=STRIPE_STATUS.get(provider_intent.status, PaymentStatus.CREATED),
            amount_minor=payload.amount_minor, currency=payload.currency,
            captured_amount_minor=provider_intent.amount_received,
            provider_client_secret=provider_intent.client_secret,
            metadata_=payload.metadata,
        ))
        record.response_code = 201
        record.response_body = {"id": str(payment.id)}
        await self.session.commit()
        return self._view(payment)

    async def get(self, payment_id: uuid.UUID) -> PaymentView:
        payment = await self.repo.get(payment_id)
        if payment is None:
            raise PaymentNotFound("Payment not found")
        return self._view(payment)

    async def capture(self, payment_id: uuid.UUID, amount_minor: int | None, key: str) -> PaymentView:
        payment = await self.repo.get(payment_id, lock=True)
        if payment is None:
            raise PaymentNotFound("Payment not found")
        if payment.status == PaymentStatus.CAPTURED:
            return self._view(payment)
        if payment.status != PaymentStatus.AUTHORIZED or not payment.provider_payment_id:
            raise InvalidPaymentState("Only an authorized payment can be captured")
        if amount_minor is not None and amount_minor > payment.amount_minor:
            raise InvalidPaymentState("Capture amount exceeds authorized amount")
        intent = await self.provider.capture_intent(
            payment.provider_payment_id, amount_minor=amount_minor, idempotency_key=key
        )
        payment.status = STRIPE_STATUS.get(intent.status, payment.status)
        payment.captured_amount_minor = intent.amount_received
        await self.session.commit()
        return self._view(payment)

    async def process_webhook(self, body: bytes, signature: str) -> tuple[str, bool]:
        event = self.provider.verify_webhook(body, signature)
        event_id, event_type = event["id"], event["type"]
        await self.repo.lock_key("stripe_event", event_id)
        if await self.repo.event_exists("stripe", event_id):
            return event_id, True
        obj: dict[str, Any] = event.get("data", {}).get("object", {})
        provider_id = obj.get("id") if obj.get("object") == "payment_intent" else None
        payment = await self.repo.get_by_provider_id(provider_id, lock=True) if provider_id else None
        if payment:
            if event_type == "payment_intent.payment_failed":
                payment.status = PaymentStatus.FAILED
                payment.failure_code = obj.get("last_payment_error", {}).get("code")
            elif event_type == "payment_intent.canceled":
                payment.status = PaymentStatus.CANCELED
            elif event_type.startswith("payment_intent."):
                payment.status = STRIPE_STATUS.get(obj.get("status", ""), payment.status)
                payment.captured_amount_minor = obj.get(
                    "amount_received", payment.captured_amount_minor
                )
        await self.repo.add_event(
            provider="stripe", event_id=event_id, event_type=event_type,
            payload=event, payment_id=payment.id if payment else None,
        )
        await self.session.commit()
        return event_id, False

    @staticmethod
    def _hash(value: dict[str, Any]) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _view(payment: Payment) -> PaymentView:
        return PaymentView(
            id=payment.id, booking_id=payment.booking_id, provider=payment.provider,
            status=payment.status, amount_minor=payment.amount_minor, currency=payment.currency,
            captured_amount_minor=payment.captured_amount_minor,
            client_secret=payment.provider_client_secret, failure_code=payment.failure_code,
            created_at=payment.created_at, updated_at=payment.updated_at,
        )
