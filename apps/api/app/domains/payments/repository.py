import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .models import IdempotencyRecord, Payment, PaymentEvent


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def lock_key(self, namespace: str, key: str) -> None:
        """Serialize idempotent operations without holding application-process locks."""
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key": f"{namespace}:{key}"},
        )

    async def get(self, payment_id: uuid.UUID, *, lock: bool = False) -> Payment | None:
        query = select(Payment).where(Payment.id == payment_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def get_by_provider_id(self, provider_id: str, *, lock: bool = False) -> Payment | None:
        query = select(Payment).where(Payment.provider_payment_id == provider_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query)

    async def get_idempotency(self, operation: str, key: str) -> IdempotencyRecord | None:
        return await self.session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == key,
            )
        )

    async def add_idempotency(self, record: IdempotencyRecord) -> None:
        self.session.add(record)
        await self.session.flush()

    async def event_exists(self, provider: str, event_id: str) -> bool:
        event = await self.session.scalar(
            select(PaymentEvent.id).where(
                PaymentEvent.provider == provider,
                PaymentEvent.provider_event_id == event_id,
            )
        )
        return event is not None

    async def add_event(
        self, *, provider: str, event_id: str, event_type: str,
        payload: dict[str, Any], payment_id: uuid.UUID | None,
    ) -> None:
        self.session.add(PaymentEvent(
            provider=provider, provider_event_id=event_id, event_type=event_type,
            payload=payload, payment_id=payment_id,
        ))
        await self.session.flush()
