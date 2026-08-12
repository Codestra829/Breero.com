import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import settings
from app.db.session import SessionLocal
from app.domains.booking.models import Booking, BookingStatus
from app.domains.common.outbox_service import OutboxService
from app.domains.finance.service import FinanceService
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
            adapter = OdooAdapter()
            email = EmailAdapter()
            notification_events = {
                "email_verification_requested",
                "password_reset_requested",
                "password_changed",
                "payment_captured",
                "refund_created",
            }

            async def deliver(event):
                aggregate = event.aggregate_type.lower()
                if event.event_type in notification_events:
                    await email.send(event.event_type, event.payload)
                    return
                if event.aggregate_type == "public_submission" and not settings.odoo_enabled:
                    # BREERO has durably accepted the form. Delivery remains pending
                    # configuration without turning a missing optional CRM into data loss.
                    return
                if aggregate == "public_submission":
                    await adapter.upsert(aggregate, event.payload)
                    return
                if aggregate in {"customer", "vendor", "booking", "job", "payment", "payout"}:
                    await adapter.upsert(aggregate, event.payload)
                else:
                    await adapter.execute("breero.event", "create", [[event.payload]])

            return await OutboxService(session).process(deliver)

    return asyncio.run(run())


@celery_app.task(name="app.workers.tasks.release_earnings")
def release_earnings() -> int:
    async def run() -> int:
        async with SessionLocal() as session:
            return await FinanceService(session).release_eligible()

    return asyncio.run(run())


@celery_app.task(name="app.workers.tasks.generate_weekly_payout_candidates")
def generate_weekly_payout_candidates() -> str:
    async def run() -> str:
        async with SessionLocal() as session:
            try:
                batch = await FinanceService(session).create_batch("USD")
                return str(batch.id)
            except Exception as exc:
                # A no-candidate week is expected; unexpected task failures remain visible in Celery.
                if getattr(exc, "status_code", None) == 409:
                    return "no_candidates"
                raise

    return asyncio.run(run())
