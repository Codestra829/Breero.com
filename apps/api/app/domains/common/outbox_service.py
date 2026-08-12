import uuid
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .outbox import AuditLog, EventStatus, IntegrationEvent

MAX_ATTEMPTS = 5
DEFAULT_LEASE_SECONDS = 300


class OutboxService:
    def __init__(self, session: AsyncSession): self.session = session

    async def claim(
        self,
        limit: int = 50,
        *,
        now: datetime | None = None,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> list[IntegrationEvent]:
        now = now or datetime.now(UTC)
        events = list((await self.session.scalars(
            select(IntegrationEvent).where(
                or_(
                    and_(
                        IntegrationEvent.status == EventStatus.PENDING,
                        IntegrationEvent.next_attempt_at <= now,
                    ),
                    and_(
                        IntegrationEvent.status == EventStatus.PROCESSING,
                        IntegrationEvent.lease_expires_at <= now,
                    ),
                )
            ).order_by(IntegrationEvent.created_at).with_for_update(skip_locked=True).limit(limit)
        )).all())
        for event in events:
            event.status = EventStatus.PROCESSING
            event.claimed_at = now
            event.lease_expires_at = now + timedelta(seconds=lease_seconds)
            event.claim_token = uuid.uuid4()
            event.attempt_count += 1
        # Commit makes the claim visible before slow network work; competing workers cannot claim it.
        await self.session.commit()
        return events

    async def process(self, deliver: Callable[[IntegrationEvent], Awaitable[None]], limit=50) -> int:
        events = await self.claim(limit)
        for event in events:
            try:
                await deliver(event)
                event.status = EventStatus.DELIVERED
                event.processed_at = datetime.now(UTC)
                event.last_error = None
            except Exception as exc:
                event.last_error = str(exc)[:2000]
                if event.attempt_count >= MAX_ATTEMPTS:
                    event.status = EventStatus.DEAD_LETTER
                    event.processed_at = datetime.now(UTC)
                else:
                    event.status = EventStatus.PENDING
                    event.next_attempt_at = datetime.now(UTC) + timedelta(
                        minutes=min(2 ** (event.attempt_count - 1), 60)
                    )
            event.lease_expires_at = None
            event.claim_token = None
            await self.session.commit()
        return len(events)

    async def retry(self, event_id: uuid.UUID, actor_id: uuid.UUID) -> IntegrationEvent:
        event = await self.session.scalar(
            select(IntegrationEvent).where(IntegrationEvent.id == event_id).with_for_update()
        )
        if not event:
            raise LookupError("Integration event not found")
        if event.status not in (EventStatus.DEAD_LETTER, EventStatus.FAILED):
            raise ValueError("Only failed integration events can be retried")
        event.status = EventStatus.PENDING
        event.attempt_count = 0
        event.next_attempt_at = datetime.now(UTC)
        event.processed_at = None
        event.claimed_at = None
        event.lease_expires_at = None
        event.claim_token = None
        self.session.add(AuditLog(actor_id=actor_id, action="integration.retry",
            resource_type="integration_event", resource_id=event.id,
            metadata_json={"previous_error": event.last_error}, created_at=datetime.now(UTC)))
        await self.session.commit()
        return event
