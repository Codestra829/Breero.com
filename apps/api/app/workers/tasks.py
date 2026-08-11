import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.booking.models import Booking, BookingStatus
from app.domains.common.outbox import EventStatus, IntegrationEvent
from app.integrations.email import EmailAdapter
from app.integrations.odoo import OdooAdapter
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.expire_bookings")
def expire_bookings() -> int:
    async def run() -> int:
        async with SessionLocal() as session:
            rows = list(
                (
                    await session.scalars(
                        select(Booking)
                        .where(
                            Booking.status == BookingStatus.PENDING_PAYMENT,
                            Booking.expires_at < datetime.now(UTC),
                        )
                        .with_for_update(skip_locked=True)
                    )
                ).all()
            )
            for booking in rows:
                booking.status = BookingStatus.EXPIRED
            await session.commit()
            return len(rows)

    return asyncio.run(run())


@celery_app.task(
    name="app.workers.tasks.publish_outbox",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
)
def publish_outbox() -> int:
    async def run() -> int:
        async with SessionLocal() as session:
            events = list(
                (
                    await session.scalars(
                        select(IntegrationEvent)
                        .where(
                            IntegrationEvent.status == EventStatus.PENDING,
                            IntegrationEvent.available_at <= datetime.now(UTC),
                        )
                        .with_for_update(skip_locked=True)
                        .limit(50)
                    )
                ).all()
            )
            adapter = OdooAdapter()
            email = EmailAdapter()
            notification_events = {
                "email_verification_requested",
                "password_reset_requested",
                "password_changed",
                "payment_captured",
                "refund_created",
            }
            for event in events:
                event.status = EventStatus.PROCESSING
                event.attempts += 1
                try:
                    if event.event_type in notification_events:
                        await email.send(event.event_type, event.payload)
                    else:
                        await adapter.execute("breero.event", "create", [[event.payload]])
                    event.status = EventStatus.DELIVERED
                    event.delivered_at = datetime.now(UTC)
                except Exception as exc:
                    event.status = (
                        EventStatus.FAILED if event.attempts >= 5 else EventStatus.PENDING
                    )
                    event.last_error = str(exc)[:2000]
            await session.commit()
            return len(events)

    return asyncio.run(run())
