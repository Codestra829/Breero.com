"""production query indexes and schema corrections

Revision ID: 008_production_readiness
Revises: 007_backend_merge
"""

import sqlalchemy as sa
from alembic import op

revision = "008_production_readiness"
down_revision = "007_backend_merge"
branch_labels = None
depends_on = None

INDEXES = {
    "ix_bookings_status_window_start": "bookings(status, window_start)",
    "ix_bookings_customer_created_at": "bookings(customer_id, created_at DESC)",
    "ix_jobs_status_scheduled_start": "jobs(status, scheduled_start)",
    "ix_jobs_vendor_status_scheduled": "jobs(vendor_id, status, scheduled_start)",
    "ix_jobs_worker_status_scheduled": "jobs(worker_id, status, scheduled_start)",
    "ix_dispatch_offers_status_expires_at": "dispatch_offers(status, expires_at)",
    "ix_vendor_earnings_eligible": "vendor_earnings(currency, status, available_at)",
    "ix_payout_batches_status_created_at": "payout_batches(status, created_at DESC)",
}


def upgrade() -> None:
    op.add_column("bookings", sa.Column("idempotency_request_hash", sa.String(64), nullable=True))
    # Existing keys predate request fingerprints. They remain replayable, while all new keys
    # enforce key+intent equivalence.
    op.execute("UPDATE bookings SET idempotency_request_hash = 'legacy'")
    op.alter_column("bookings", "idempotency_request_hash", nullable=False)
    op.execute("UPDATE addresses SET geocoding_provider = 'provided' WHERE geocoding_provider IS NULL")
    op.execute("ALTER TABLE addresses ALTER COLUMN geocoding_provider SET DEFAULT 'provided'")
    op.execute("ALTER TABLE addresses ALTER COLUMN geocoding_provider SET NOT NULL")
    for name, expression in INDEXES.items():
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {expression}")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_service_areas_boundary ON service_areas USING gist(boundary)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_service_areas_boundary")
    for name in reversed(INDEXES):
        op.execute(f"DROP INDEX IF EXISTS {name}")
    op.execute("ALTER TABLE addresses ALTER COLUMN geocoding_provider DROP NOT NULL")
    op.execute("ALTER TABLE addresses ALTER COLUMN geocoding_provider DROP DEFAULT")
    op.drop_column("bookings", "idempotency_request_hash")
