"""add typed Odoo CRM delivery acknowledgements

Revision ID: 013_odoo_crm_delivery
Revises: 012_service_area_dimensions
"""

import sqlalchemy as sa
from alembic import op

revision = "013_odoo_crm_delivery"
down_revision = "012_service_area_dimensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for value in ("RETRYING", "FAILED_RETRYABLE", "FAILED_TERMINAL"):
        op.execute(f"ALTER TYPE integration_event_status ADD VALUE IF NOT EXISTS '{value}'")
    op.add_column("integration_events", sa.Column("aggregate_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("integration_events", sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("integration_events", sa.Column("idempotency_key", sa.String(255)))
    op.add_column("integration_events", sa.Column("last_error_code", sa.String(80)))
    op.add_column("integration_events", sa.Column("last_error_at", sa.DateTime(timezone=True)))
    op.add_column("integration_events", sa.Column("external_model", sa.String(120)))
    op.add_column("integration_events", sa.Column("external_record_id", sa.String(120)))
    op.create_index("ix_integration_events_idempotency_key", "integration_events", ["idempotency_key"], unique=True)
    # Legacy rows predate versioned idempotency. Enforce the tuple for newly versioned events only.
    op.execute("CREATE UNIQUE INDEX uq_integration_event_version ON integration_events (event_type, aggregate_id, aggregate_version) WHERE idempotency_key IS NOT NULL")


def downgrade() -> None:
    op.drop_index("uq_integration_event_version", table_name="integration_events")
    op.drop_index("ix_integration_events_idempotency_key", table_name="integration_events")
    for name in ("external_record_id", "external_model", "last_error_at", "last_error_code", "idempotency_key", "schema_version", "aggregate_version"):
        op.drop_column("integration_events", name)
