"""jobs, workforce, dispatch, work requests, and payouts

Revision ID: 004_operations
Revises: 003_payments
"""

from alembic import op

revision = "004_operations"
down_revision = "003_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE vendor_status AS ENUM ('PENDING','ACTIVE','SUSPENDED','REJECTED')")
    op.execute("CREATE TYPE worker_status AS ENUM ('INVITED','ACTIVE','INACTIVE')")
    op.execute(
        "CREATE TYPE job_status AS ENUM ('CREATED','MATCHING','OFFERED','ASSIGNED','EN_ROUTE','ON_SITE','DIAGNOSING','AWAITING_APPROVAL','IN_PROGRESS','COMPLETED','CANCELLED')"
    )
    op.execute(
        "CREATE TYPE work_request_status AS ENUM ('DRAFT','SUBMITTED','APPROVED','DECLINED','PAID','CANCELLED')"
    )
    op.execute(
        "CREATE TYPE offer_status AS ENUM ('PENDING','ACCEPTED','DECLINED','EXPIRED','WITHDRAWN')"
    )
    op.execute("CREATE TYPE assignment_status AS ENUM ('ACTIVE','RELEASED','COMPLETED')")
    op.execute(
        "CREATE TYPE earning_status AS ENUM ('PENDING','AVAILABLE','BATCHED','PAID','REVERSED')"
    )
    op.execute(
        "CREATE TYPE payout_status AS ENUM ('DRAFT','PENDING_APPROVAL','APPROVED','PROCESSING','PAID','FAILED')"
    )
    op.execute("""
      CREATE TABLE vendors (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), legal_name varchar(180) NOT NULL,
        display_name varchar(120) NOT NULL, email varchar(320) NOT NULL UNIQUE,
        phone varchar(32) NOT NULL, status vendor_status NOT NULL,
        service_radius_meters integer NOT NULL DEFAULT 40000,
        home_location geography(POINT,4326), capabilities jsonb NOT NULL DEFAULT '[]',
        payout_profile_ref varchar(255), odoo_partner_id varchar(64),
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_vendors_status ON vendors(status); CREATE INDEX ix_vendors_home_location ON vendors USING gist(home_location)
    """)
    op.execute("""
      CREATE TABLE workers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), vendor_id uuid NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
        user_id uuid UNIQUE, first_name varchar(80) NOT NULL, last_name varchar(80) NOT NULL,
        email varchar(320) NOT NULL, phone varchar(32) NOT NULL, status worker_status NOT NULL,
        skills jsonb NOT NULL DEFAULT '[]', current_location geography(POINT,4326),
        location_updated_at timestamptz, available boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(vendor_id,email)
      ); CREATE INDEX ix_workers_vendor_id ON workers(vendor_id); CREATE INDEX ix_workers_status ON workers(status);
      CREATE INDEX ix_workers_current_location ON workers USING gist(current_location)
    """)
    op.execute("""
      CREATE TABLE worker_location_events (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), worker_id uuid NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
        location geography(POINT,4326) NOT NULL, accuracy_meters integer,
        recorded_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_worker_location_events_worker_id ON worker_location_events(worker_id);
      CREATE INDEX ix_worker_location_events_recorded_at ON worker_location_events(recorded_at)
    """)
    op.execute("""
      CREATE TABLE jobs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), booking_id uuid NOT NULL UNIQUE,
        customer_id uuid, service_id uuid NOT NULL, address_id uuid NOT NULL, status job_status NOT NULL,
        scheduled_start timestamptz NOT NULL, scheduled_end timestamptz NOT NULL,
        vendor_id uuid, worker_id uuid, version integer NOT NULL DEFAULT 1,
        diagnostic_notes text, completion_notes text, completed_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_jobs_status ON jobs(status); CREATE INDEX ix_jobs_customer_id ON jobs(customer_id);
      CREATE INDEX ix_jobs_service_id ON jobs(service_id); CREATE INDEX ix_jobs_vendor_id ON jobs(vendor_id);
      CREATE INDEX ix_jobs_worker_id ON jobs(worker_id); CREATE INDEX ix_jobs_scheduled_start ON jobs(scheduled_start)
    """)
    op.execute("""
      CREATE TABLE job_events (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        from_status job_status, to_status job_status NOT NULL, actor_id uuid, actor_type varchar(32) NOT NULL,
        reason text, metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_job_events_job_id ON job_events(job_id)
    """)
    op.execute("""
      CREATE TABLE work_requests (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        status work_request_status NOT NULL, description text NOT NULL, line_items jsonb NOT NULL,
        subtotal_minor integer NOT NULL CHECK(subtotal_minor >= 0), tax_minor integer NOT NULL CHECK(tax_minor >= 0),
        total_minor integer NOT NULL CHECK(total_minor >= 0), currency varchar(3) NOT NULL,
        payment_id uuid, customer_decided_at timestamptz, created_by uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_work_requests_job_id ON work_requests(job_id); CREATE INDEX ix_work_requests_status ON work_requests(status)
    """)
    op.execute("""
      CREATE TABLE dispatch_offers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        vendor_id uuid NOT NULL REFERENCES vendors(id), worker_id uuid REFERENCES workers(id),
        status offer_status NOT NULL, round integer NOT NULL DEFAULT 1, score integer NOT NULL,
        score_detail jsonb NOT NULL DEFAULT '{}', expires_at timestamptz NOT NULL,
        responded_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(job_id,vendor_id,round)
      ); CREATE INDEX ix_dispatch_offers_job_id ON dispatch_offers(job_id); CREATE INDEX ix_dispatch_offers_vendor_id ON dispatch_offers(vendor_id);
      CREATE INDEX ix_dispatch_offers_status ON dispatch_offers(status); CREATE INDEX ix_dispatch_offers_expires_at ON dispatch_offers(expires_at)
    """)
    op.execute("""
      CREATE TABLE assignments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), job_id uuid NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        offer_id uuid REFERENCES dispatch_offers(id), vendor_id uuid NOT NULL REFERENCES vendors(id),
        worker_id uuid NOT NULL REFERENCES workers(id), status assignment_status NOT NULL,
        assigned_by uuid, assigned_at timestamptz NOT NULL DEFAULT now(), released_at timestamptz
      ); CREATE INDEX ix_assignments_job_id ON assignments(job_id); CREATE INDEX ix_assignments_vendor_id ON assignments(vendor_id);
      CREATE INDEX ix_assignments_worker_id ON assignments(worker_id);
      CREATE UNIQUE INDEX uq_active_assignment_job ON assignments(job_id) WHERE status = 'ACTIVE'
    """)
    op.execute("""
      CREATE TABLE payout_batches (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), reference varchar(64) NOT NULL UNIQUE,
        status payout_status NOT NULL, currency varchar(3) NOT NULL, total_minor integer NOT NULL,
        earning_count integer NOT NULL, approved_by uuid, approved_at timestamptz,
        provider_reference varchar(255), failure_reason varchar(500), created_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_payout_batches_status ON payout_batches(status)
    """)
    op.execute("""
      CREATE TABLE vendor_earnings (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), vendor_id uuid NOT NULL REFERENCES vendors(id),
        job_id uuid NOT NULL REFERENCES jobs(id) UNIQUE, gross_minor integer NOT NULL CHECK(gross_minor >= 0),
        fee_minor integer NOT NULL CHECK(fee_minor >= 0), net_minor integer NOT NULL CHECK(net_minor >= 0),
        currency varchar(3) NOT NULL, status earning_status NOT NULL, available_at timestamptz NOT NULL,
        payout_batch_id uuid REFERENCES payout_batches(id), created_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_vendor_earnings_vendor_id ON vendor_earnings(vendor_id);
      CREATE INDEX ix_vendor_earnings_status ON vendor_earnings(status); CREATE INDEX ix_vendor_earnings_payout_batch_id ON vendor_earnings(payout_batch_id)
    """)


def downgrade() -> None:
    for table in [
        "vendor_earnings",
        "payout_batches",
        "assignments",
        "dispatch_offers",
        "work_requests",
        "job_events",
        "jobs",
        "worker_location_events",
        "workers",
        "vendors",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table}")
    for type_name in [
        "payout_status",
        "earning_status",
        "assignment_status",
        "offer_status",
        "work_request_status",
        "job_status",
        "worker_status",
        "vendor_status",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {type_name}")
