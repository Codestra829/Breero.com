"""Add quote-only, operator-confirmed scheduling controls.

Revision ID: 014_quote_only_manual_scheduling
Revises: 013_odoo_crm_delivery
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "014_quote_only_manual_scheduling"
down_revision = "013_odoo_crm_delivery"
branch_labels = None
depends_on = None


NEW_BOOKING_STATES = (
    "REQUESTED",
    "PENDING_MANUAL_DISPATCH",
    "TENTATIVE_HOLD",
    "PROVIDER_ASSIGNED",
    "SCHEDULED",
)


def upgrade() -> None:
    # PostgreSQL requires newly-added enum labels to be committed before use.
    with op.get_context().autocommit_block():
        for value in NEW_BOOKING_STATES:
            op.execute(f"ALTER TYPE booking_status ADD VALUE IF NOT EXISTS '{value}'")

    op.add_column("addresses", sa.Column("timezone", sa.String(64)))
    op.add_column("addresses", sa.Column("validated_at", sa.DateTime(timezone=True)))
    op.alter_column("bookings", "legal_entity_id", existing_type=postgresql.UUID(), nullable=True)
    op.add_column("bookings", sa.Column("hold_expires_at", sa.DateTime(timezone=True)))
    op.add_column("bookings", sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    op.add_column("bookings", sa.Column("confirmed_by", postgresql.UUID()))
    op.add_column("bookings", sa.Column("cancellation_reason", sa.Text()))
    op.add_column(
        "bookings",
        sa.Column("scheduling_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_bookings_hold_expires_at", "bookings", ["hold_expires_at"])
    op.execute("UPDATE bookings SET status = 'REQUESTED' WHERE status = 'PENDING_PAYMENT'")
    op.add_column("services", sa.Column("pre_scheduling_is_bookable", sa.Boolean()))
    op.execute("UPDATE services SET pre_scheduling_is_bookable = is_bookable")
    # Requestable nationwide does not imply coverage or automatic confirmation.
    op.execute("UPDATE services SET is_bookable = true WHERE is_active")

    op.add_column(
        "vendors",
        sa.Column("covered_postal_codes", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "vendors", sa.Column("working_hours", postgresql.JSONB(), nullable=False, server_default="{}")
    )
    op.add_column("vendors", sa.Column("license_valid_until", sa.Date()))
    op.add_column("vendors", sa.Column("insurance_valid_until", sa.Date()))

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.add_column("assignments", sa.Column("scheduled_start", sa.DateTime(timezone=True)))
    op.add_column("assignments", sa.Column("scheduled_end", sa.DateTime(timezone=True)))
    op.execute(
        """
        UPDATE assignments a
           SET scheduled_start = j.scheduled_start,
               scheduled_end = j.scheduled_end
          FROM jobs j
         WHERE j.id = a.job_id
        """
    )
    op.alter_column("assignments", "scheduled_start", nullable=False)
    op.alter_column("assignments", "scheduled_end", nullable=False)
    op.execute(
        """
        ALTER TABLE assignments ADD CONSTRAINT excl_active_worker_schedule_overlap
        EXCLUDE USING gist (
            worker_id WITH =,
            tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
        ) WHERE (status = 'ACTIVE')
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE assignments DROP CONSTRAINT excl_active_worker_schedule_overlap")
    op.drop_column("assignments", "scheduled_end")
    op.drop_column("assignments", "scheduled_start")
    op.drop_column("vendors", "insurance_valid_until")
    op.drop_column("vendors", "license_valid_until")
    op.drop_column("vendors", "working_hours")
    op.drop_column("vendors", "covered_postal_codes")
    op.execute(
        "UPDATE services SET is_bookable = pre_scheduling_is_bookable "
        "WHERE pre_scheduling_is_bookable IS NOT NULL"
    )
    op.drop_column("services", "pre_scheduling_is_bookable")
    op.execute(
        """
        UPDATE bookings SET status = CASE
            WHEN status IN ('SCHEDULED', 'PROVIDER_ASSIGNED') THEN 'CONFIRMED'::booking_status
            WHEN status IN ('REQUESTED', 'PENDING_MANUAL_DISPATCH', 'TENTATIVE_HOLD')
                THEN 'CANCELLED'::booking_status
            ELSE status
        END
        """
    )
    op.drop_index("ix_bookings_hold_expires_at", table_name="bookings")
    op.drop_column("bookings", "scheduling_version")
    op.drop_column("bookings", "cancellation_reason")
    op.drop_column("bookings", "confirmed_by")
    op.drop_column("bookings", "confirmed_at")
    op.drop_column("bookings", "hold_expires_at")
    op.execute(
        """
        INSERT INTO legal_entities (id, code, name, currency, active)
        SELECT gen_random_uuid(), 'ROLLBACK-MANUAL', 'Manual dispatch rollback', 'USD', false
        WHERE EXISTS (SELECT 1 FROM bookings WHERE legal_entity_id IS NULL)
          AND NOT EXISTS (SELECT 1 FROM legal_entities WHERE code = 'ROLLBACK-MANUAL')
        """
    )
    op.execute(
        """
        UPDATE bookings
           SET legal_entity_id = (SELECT id FROM legal_entities WHERE code = 'ROLLBACK-MANUAL')
         WHERE legal_entity_id IS NULL
        """
    )
    op.alter_column("bookings", "legal_entity_id", existing_type=postgresql.UUID(), nullable=False)
    op.drop_column("addresses", "validated_at")
    op.drop_column("addresses", "timezone")

    op.execute("ALTER TYPE booking_status RENAME TO booking_status_with_scheduling")
    op.execute(
        "CREATE TYPE booking_status AS ENUM "
        "('PENDING_PAYMENT', 'CONFIRMED', 'CANCELLED', 'EXPIRED')"
    )
    op.execute(
        "ALTER TABLE bookings ALTER COLUMN status TYPE booking_status "
        "USING status::text::booking_status"
    )
    op.execute("DROP TYPE booking_status_with_scheduling")
