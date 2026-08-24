"""privacy requests, consent evidence, and suppression

Revision ID: 016_privacy_consent_controls
Revises: 015_scheduling_without_payments
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "016_privacy_consent_controls"
down_revision = "015_scheduling_without_payments"
branch_labels = None
depends_on = None


def upgrade():
    status = postgresql.ENUM(
        "RECEIVED",
        "VERIFYING",
        "IN_PROGRESS",
        "COMPLETED",
        "DENIED",
        "APPEALED",
        name="privacy_request_status",
        create_type=False,
    )
    op.execute(
        "CREATE TYPE privacy_request_status AS ENUM "
        "('RECEIVED','VERIFYING','IN_PROGRESS','COMPLETED','DENIED','APPEALED')"
    )
    op.create_table(
        "privacy_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("request_type", sa.String(40), nullable=False),
        sa.Column("normalized_email", sa.String(320), nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("verification_state", sa.String(40), nullable=False),
        sa.Column("receipt_token_hash", sa.String(64), nullable=False),
        sa.Column("jurisdiction", sa.String(3)),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("source_ip_hash", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("history", postgresql.JSONB, nullable=False),
    )
    op.create_index("ix_privacy_requests_due_at", "privacy_requests", ["due_at"])
    op.create_index(
        "ix_privacy_requests_normalized_email", "privacy_requests", ["normalized_email"]
    )
    op.create_index("ix_privacy_requests_request_type", "privacy_requests", ["request_type"])
    op.create_table(
        "consent_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("destination_hash", sa.String(64), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True)),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_ip_hash", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("disclosure_text", sa.Text, nullable=False),
        sa.Column("policy_versions", postgresql.JSONB, nullable=False),
        sa.Column("evidence", postgresql.JSONB, nullable=False),
    )
    op.create_index("ix_consent_events_destination_hash", "consent_events", ["destination_hash"])
    op.create_index("ix_consent_events_customer_id", "consent_events", ["customer_id"])
    op.create_index("ix_consent_events_purpose", "consent_events", ["purpose"])
    op.create_index("ix_consent_events_occurred_at", "consent_events", ["occurred_at"])
    op.create_table(
        "communication_suppressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("destination_hash", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("reason", sa.String(80), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("source", sa.String(80), nullable=False),
        sa.UniqueConstraint("destination_hash", "channel", "purpose"),
    )
    op.create_index(
        "ix_communication_suppressions_destination_hash",
        "communication_suppressions",
        ["destination_hash"],
    )


def downgrade():
    op.drop_table("communication_suppressions")
    op.drop_table("consent_events")
    op.drop_table("privacy_requests")
    postgresql.ENUM(name="privacy_request_status").drop(op.get_bind())
