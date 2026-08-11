"""configurable finance and resilient integrations

Revision ID: 006_finance_integrations
Revises: 005_booking_integrations
"""
from alembic import op

revision = "006_finance_integrations"
down_revision = "005_booking_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE compensation_method AS ENUM ('FIXED_MINOR','PERCENTAGE','SERVICE_RATE')")
    op.execute("CREATE TYPE earning_adjustment_type AS ENUM ('REFUND','DISPUTE','MANUAL','REVERSAL')")
    for value in ("HELD", "APPROVED", "CANCELLED"):
        op.execute(f"ALTER TYPE earning_status ADD VALUE IF NOT EXISTS '{value}'")
    op.execute("ALTER TYPE payout_status ADD VALUE IF NOT EXISTS 'CANCELLED'")
    op.execute("ALTER TYPE integration_event_status ADD VALUE IF NOT EXISTS 'DEAD_LETTER'")
    op.execute("""
      CREATE TABLE vendor_compensation_plans (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), vendor_id uuid NOT NULL REFERENCES vendors(id),
        name varchar(160) NOT NULL, method compensation_method NOT NULL, fixed_minor integer,
        percentage_bps integer, currency varchar(3) NOT NULL DEFAULT 'USD', hold_days integer NOT NULL DEFAULT 7,
        active boolean NOT NULL DEFAULT true, effective_from timestamptz NOT NULL, effective_to timestamptz,
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
        CHECK (hold_days >= 0), CHECK (percentage_bps IS NULL OR percentage_bps BETWEEN 0 AND 10000)
      ); CREATE INDEX ix_vendor_compensation_plans_vendor_id ON vendor_compensation_plans(vendor_id);
      CREATE INDEX ix_vendor_compensation_plans_active ON vendor_compensation_plans(active)
    """)
    op.execute("""
      CREATE TABLE vendor_service_compensations (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), plan_id uuid NOT NULL REFERENCES vendor_compensation_plans(id) ON DELETE CASCADE,
        service_id uuid NOT NULL, rate_minor integer NOT NULL CHECK(rate_minor >= 0), currency varchar(3) NOT NULL DEFAULT 'USD',
        UNIQUE(plan_id, service_id)
      ); CREATE INDEX ix_vendor_service_compensations_plan_id ON vendor_service_compensations(plan_id);
      CREATE INDEX ix_vendor_service_compensations_service_id ON vendor_service_compensations(service_id)
    """)
    op.execute("""
      CREATE TABLE compensation_snapshots (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), plan_id uuid, vendor_id uuid NOT NULL, service_id uuid NOT NULL,
        method compensation_method NOT NULL, rule_json jsonb NOT NULL, gross_minor integer NOT NULL,
        compensation_minor integer NOT NULL, currency varchar(3) NOT NULL, hold_days integer NOT NULL,
        committed_at timestamptz NOT NULL
      ); CREATE INDEX ix_compensation_snapshots_plan_id ON compensation_snapshots(plan_id);
      CREATE INDEX ix_compensation_snapshots_vendor_id ON compensation_snapshots(vendor_id);
      CREATE INDEX ix_compensation_snapshots_service_id ON compensation_snapshots(service_id)
    """)
    op.execute("ALTER TABLE vendor_earnings ADD COLUMN compensation_snapshot_id uuid REFERENCES compensation_snapshots(id)")
    op.execute("""
      INSERT INTO compensation_snapshots
        (id, plan_id, vendor_id, service_id, method, rule_json, gross_minor,
         compensation_minor, currency, hold_days, committed_at)
      SELECT e.id, NULL, e.vendor_id, j.service_id, 'FIXED_MINOR',
             jsonb_build_object('legacy_migration', true, 'net_minor', e.net_minor),
             e.gross_minor, e.net_minor, e.currency, 0, e.created_at
      FROM vendor_earnings e JOIN jobs j ON j.id = e.job_id
    """)
    op.execute("UPDATE vendor_earnings SET compensation_snapshot_id = id")
    op.execute("ALTER TABLE vendor_earnings ALTER COLUMN compensation_snapshot_id SET NOT NULL")
    op.execute("ALTER TABLE vendor_earnings ADD COLUMN adjustment_total_minor integer NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE vendor_earnings ADD CONSTRAINT uq_vendor_earnings_compensation_snapshot_id UNIQUE(compensation_snapshot_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vendor_earnings_available_at ON vendor_earnings(available_at)")
    op.execute("""
      CREATE TABLE earning_adjustments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), earning_id uuid NOT NULL REFERENCES vendor_earnings(id) ON DELETE RESTRICT,
        adjustment_type earning_adjustment_type NOT NULL, amount_minor integer NOT NULL, reason text NOT NULL,
        idempotency_key varchar(128) NOT NULL, actor_id uuid, created_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE(earning_id, idempotency_key)
      ); CREATE INDEX ix_earning_adjustments_earning_id ON earning_adjustments(earning_id)
    """)
    op.execute("ALTER TABLE payout_batches ADD COLUMN reviewed_by uuid")
    op.execute("ALTER TABLE payout_batches ADD COLUMN reviewed_at timestamptz")
    op.execute("ALTER TABLE payout_batches ADD COLUMN idempotency_key varchar(128) UNIQUE")
    op.execute("ALTER TABLE payout_batches ADD COLUMN submitted_at timestamptz")
    op.execute("ALTER TABLE payout_batches ADD COLUMN provider_transfer_id varchar(255) UNIQUE")
    op.execute("ALTER TABLE payout_batches ADD COLUMN provider_status varchar(80)")
    op.execute("DROP INDEX IF EXISTS ix_integration_events_claim")
    op.execute("ALTER TABLE integration_events RENAME COLUMN attempts TO attempt_count")
    op.execute("ALTER TABLE integration_events RENAME COLUMN available_at TO next_attempt_at")
    op.execute("ALTER TABLE integration_events RENAME COLUMN delivered_at TO processed_at")
    op.execute("ALTER TABLE integration_events ADD COLUMN claimed_at timestamptz")
    op.execute("CREATE INDEX ix_integration_events_claim ON integration_events(status, next_attempt_at, created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_integration_events_claim")
    op.execute("ALTER TABLE integration_events DROP COLUMN claimed_at")
    op.execute("ALTER TABLE integration_events RENAME COLUMN processed_at TO delivered_at")
    op.execute("ALTER TABLE integration_events RENAME COLUMN next_attempt_at TO available_at")
    op.execute("ALTER TABLE integration_events RENAME COLUMN attempt_count TO attempts")
    op.execute("CREATE INDEX ix_integration_events_claim ON integration_events(status, available_at, created_at)")
    for column in ("provider_status", "provider_transfer_id", "submitted_at", "idempotency_key", "reviewed_at", "reviewed_by"):
        op.execute(f"ALTER TABLE payout_batches DROP COLUMN {column}")
    op.execute("DROP TABLE earning_adjustments")
    op.execute("ALTER TABLE vendor_earnings DROP COLUMN adjustment_total_minor")
    op.execute("ALTER TABLE vendor_earnings DROP COLUMN compensation_snapshot_id")
    op.execute("DROP TABLE compensation_snapshots")
    op.execute("DROP TABLE vendor_service_compensations")
    op.execute("DROP TABLE vendor_compensation_plans")
    op.execute("DROP TYPE earning_adjustment_type")
    op.execute("DROP TYPE compensation_method")
