import asyncio
import os
import uuid

import psycopg
import pytest
from psycopg.errors import UniqueViolation

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="requires real PostgreSQL",
)


def dsn() -> str:
    return os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)


@pytest.mark.asyncio
async def test_two_booking_transactions_serialize_same_capacity_slot():
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    key = f"booking-slot:{uuid.uuid4()}"
    try:
        await first.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (key,))
        waiter = asyncio.create_task(
            second.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (key,))
        )
        await asyncio.sleep(0.05)
        assert not waiter.done(), "second capacity decision must wait for the first transaction"
        await first.commit()
        await asyncio.wait_for(waiter, 1)
    finally:
        await second.rollback()
        await first.close()
        await second.close()


@pytest.mark.asyncio
async def test_simultaneous_stripe_webhook_has_one_durable_event():
    event_id = f"evt_{uuid.uuid4().hex}"
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    insert = """INSERT INTO payment_events
        (id, provider, provider_event_id, event_type, payload)
        VALUES (%s, 'stripe', %s, 'payment_intent.succeeded', '{}'::jsonb)"""
    try:
        await first.execute(insert, (uuid.uuid4(), event_id))
        duplicate = asyncio.create_task(second.execute(insert, (uuid.uuid4(), event_id)))
        await asyncio.sleep(0.05)
        assert not duplicate.done()
        await first.commit()
        with pytest.raises(UniqueViolation):
            await duplicate
    finally:
        await second.rollback()
        await first.close()
        await second.close()


@pytest.mark.asyncio
async def test_two_workers_cannot_claim_same_outbox_event():
    event_id = uuid.uuid4()
    setup = await psycopg.AsyncConnection.connect(dsn())
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    try:
        await setup.execute(
            """INSERT INTO integration_events
            (id, aggregate_type, aggregate_id, event_type, payload, status,
             attempt_count, next_attempt_at, created_at, updated_at)
            VALUES (%s, 'test', %s, 'test.event', '{}'::jsonb, 'PENDING', 0, now(), now(), now())""",
            (event_id, uuid.uuid4()),
        )
        await setup.commit()
        query = """SELECT id FROM integration_events WHERE id = %s AND status = 'PENDING'
                   FOR UPDATE SKIP LOCKED"""
        claimed = await first.execute(query, (event_id,))
        skipped = await second.execute(query, (event_id,))
        assert await claimed.fetchone() == (event_id,)
        assert await skipped.fetchone() is None
    finally:
        await first.rollback()
        await second.rollback()
        await setup.execute("DELETE FROM integration_events WHERE id = %s", (event_id,))
        await setup.commit()
        await setup.close()
        await first.close()
        await second.close()
