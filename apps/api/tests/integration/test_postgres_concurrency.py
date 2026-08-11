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


async def create_dispatch_fixture(connection):
    vendor_id, worker_id, job_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    await connection.execute(
        """INSERT INTO vendors
        (id, legal_name, display_name, email, phone, status, capabilities)
        VALUES (%s, 'Race Vendor', 'Race Vendor', %s, '+490000000', 'ACTIVE', '[]')""",
        (vendor_id, f"race-{vendor_id}@example.com"),
    )
    await connection.execute(
        """INSERT INTO workers
        (id, vendor_id, first_name, last_name, email, phone, status, skills, available)
        VALUES (%s, %s, 'Race', 'Worker', %s, '+490000001', 'ACTIVE', '[]', true)""",
        (worker_id, vendor_id, f"race-{worker_id}@example.com"),
    )
    await connection.execute(
        """INSERT INTO jobs
        (id, booking_id, service_id, address_id, status, scheduled_start, scheduled_end, version)
        VALUES (%s, %s, %s, %s, 'CREATED', now() + interval '1 day',
                now() + interval '1 day 2 hours', 1)""",
        (job_id, uuid.uuid4(), uuid.uuid4(), uuid.uuid4()),
    )
    await connection.commit()
    return vendor_id, worker_id, job_id


@pytest.mark.asyncio
async def test_simultaneous_assignment_allows_only_one_active_assignment():
    setup = await psycopg.AsyncConnection.connect(dsn())
    vendor_id, worker_id, job_id = await create_dispatch_fixture(setup)
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    insert = """INSERT INTO assignments (id, job_id, vendor_id, worker_id, status)
                VALUES (%s, %s, %s, %s, 'ACTIVE')"""
    try:
        await first.execute(insert, (uuid.uuid4(), job_id, vendor_id, worker_id))
        duplicate = asyncio.create_task(
            second.execute(insert, (uuid.uuid4(), job_id, vendor_id, worker_id))
        )
        await asyncio.sleep(0.05)
        assert not duplicate.done()
        await first.commit()
        with pytest.raises(UniqueViolation):
            await duplicate
    finally:
        await second.rollback()
        await setup.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        await setup.execute("DELETE FROM workers WHERE id = %s", (worker_id,))
        await setup.execute("DELETE FROM vendors WHERE id = %s", (vendor_id,))
        await setup.commit()
        await first.close()
        await second.close()
        await setup.close()


@pytest.mark.asyncio
async def test_simultaneous_job_transition_observes_locked_latest_state():
    setup = await psycopg.AsyncConnection.connect(dsn())
    vendor_id, worker_id, job_id = await create_dispatch_fixture(setup)
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    transition = """UPDATE jobs SET status = 'MATCHING', version = version + 1
                    WHERE id = %s AND status = 'CREATED' RETURNING version"""
    try:
        first_result = await first.execute(transition, (job_id,))
        competing = asyncio.create_task(second.execute(transition, (job_id,)))
        await asyncio.sleep(0.05)
        assert not competing.done()
        await first.commit()
        assert await first_result.fetchone() == (2,)
        second_result = await competing
        assert await second_result.fetchone() is None
    finally:
        await second.rollback()
        await setup.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        await setup.execute("DELETE FROM workers WHERE id = %s", (worker_id,))
        await setup.execute("DELETE FROM vendors WHERE id = %s", (vendor_id,))
        await setup.commit()
        await first.close()
        await second.close()
        await setup.close()


@pytest.mark.asyncio
async def test_duplicate_payout_submission_claims_batch_once():
    batch_id = uuid.uuid4()
    setup = await psycopg.AsyncConnection.connect(dsn())
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    claim = """UPDATE payout_batches SET status = 'PROCESSING', submitted_at = now()
               WHERE id = %s AND status = 'APPROVED' RETURNING id"""
    try:
        await setup.execute(
            """INSERT INTO payout_batches
            (id, reference, status, currency, total_minor, earning_count)
            VALUES (%s, %s, 'APPROVED', 'EUR', 1000, 1)""",
            (batch_id, f"race-{batch_id}"),
        )
        await setup.commit()
        first_result = await first.execute(claim, (batch_id,))
        competing = asyncio.create_task(second.execute(claim, (batch_id,)))
        await asyncio.sleep(0.05)
        assert not competing.done()
        await first.commit()
        assert await first_result.fetchone() == (batch_id,)
        second_result = await competing
        assert await second_result.fetchone() is None
    finally:
        await second.rollback()
        await setup.execute("DELETE FROM payout_batches WHERE id = %s", (batch_id,))
        await setup.commit()
        await setup.close()
        await first.close()
        await second.close()


@pytest.mark.asyncio
async def test_earning_candidate_cannot_enter_two_payout_batches():
    setup = await psycopg.AsyncConnection.connect(dsn())
    vendor_id, worker_id, job_id = await create_dispatch_fixture(setup)
    snapshot_id, earning_id = uuid.uuid4(), uuid.uuid4()
    first_batch, second_batch = uuid.uuid4(), uuid.uuid4()
    first = await psycopg.AsyncConnection.connect(dsn())
    second = await psycopg.AsyncConnection.connect(dsn())
    claim = """UPDATE vendor_earnings SET status = 'BATCHED', payout_batch_id = %s
               WHERE id = %s AND status = 'AVAILABLE' AND payout_batch_id IS NULL RETURNING id"""
    try:
        for batch_id in (first_batch, second_batch):
            await setup.execute(
                """INSERT INTO payout_batches
                (id, reference, status, currency, total_minor, earning_count)
                VALUES (%s, %s, 'DRAFT', 'EUR', 1000, 1)""",
                (batch_id, f"race-{batch_id}"),
            )
        await setup.execute(
            """INSERT INTO compensation_snapshots
            (id, vendor_id, service_id, method, rule_json, gross_minor,
             compensation_minor, currency, hold_days, committed_at)
            SELECT %s, %s, service_id, 'FIXED_MINOR', '{"fixed_minor": 1000}',
                   1000, 1000, 'EUR', 0, now() FROM jobs WHERE id = %s""",
            (snapshot_id, vendor_id, job_id),
        )
        await setup.execute(
            """INSERT INTO vendor_earnings
            (id, vendor_id, job_id, compensation_snapshot_id, gross_minor, fee_minor,
             net_minor, adjustment_total_minor, currency, status, available_at)
            VALUES (%s, %s, %s, %s, 1000, 0, 1000, 0, 'EUR', 'AVAILABLE', now())""",
            (earning_id, vendor_id, job_id, snapshot_id),
        )
        await setup.commit()
        first_result = await first.execute(claim, (first_batch, earning_id))
        competing = asyncio.create_task(second.execute(claim, (second_batch, earning_id)))
        await asyncio.sleep(0.05)
        assert not competing.done()
        await first.commit()
        assert await first_result.fetchone() == (earning_id,)
        second_result = await competing
        assert await second_result.fetchone() is None
    finally:
        await second.rollback()
        await setup.execute("DELETE FROM vendor_earnings WHERE id = %s", (earning_id,))
        await setup.execute("DELETE FROM compensation_snapshots WHERE id = %s", (snapshot_id,))
        await setup.execute(
            "DELETE FROM payout_batches WHERE id IN (%s, %s)", (first_batch, second_batch)
        )
        await setup.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        await setup.execute("DELETE FROM workers WHERE id = %s", (worker_id,))
        await setup.execute("DELETE FROM vendors WHERE id = %s", (vendor_id,))
        await setup.commit()
        await setup.close()
        await first.close()
        await second.close()
