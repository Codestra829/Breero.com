"""add payment ledger, webhook events, and idempotency records

Revision ID: 003_payments
Revises: 002_auth_catalog
Create Date: 2026-08-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003_payments"
down_revision = "002_auth_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    payment_status = postgresql.ENUM(
        "created", "requires_action", "authorized", "captured", "failed", "canceled",
        "refunded", name="payment_status", create_type=False,
    )
    payment_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(32), server_default="stripe", nullable=False),
        sa.Column("provider_payment_id", sa.String(255)),
        sa.Column("status", payment_status, server_default="created", nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("captured_amount_minor", sa.Integer(), server_default="0", nullable=False),
        sa.Column("provider_client_secret", sa.Text()),
        sa.Column("failure_code", sa.String(100)),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_minor > 0", name="ck_payments_positive_amount"),
        sa.CheckConstraint(
            "captured_amount_minor >= 0 AND captured_amount_minor <= amount_minor",
            name="ck_payments_valid_captured_amount",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.UniqueConstraint("provider", "provider_payment_id", name="uq_payments_provider_payment_id"),
    )
    op.create_index("ix_payments_booking_id_created_at", "payments", ["booking_id", "created_at"])
    op.create_table(
        "payment_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], name="fk_payment_events_payment_id_payments", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_payment_events"),
        sa.UniqueConstraint("provider", "provider_event_id", name="uq_payment_events_provider_event"),
    )
    op.create_table(
        "payment_idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_code", sa.Integer()),
        sa.Column("response_body", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_payment_idempotency_records"),
        sa.UniqueConstraint("operation", "idempotency_key", name="uq_payment_idempotency_operation_key"),
    )


def downgrade() -> None:
    op.drop_table("payment_idempotency_records")
    op.drop_table("payment_events")
    op.drop_index("ix_payments_booking_id_created_at", table_name="payments")
    op.drop_table("payments")
    postgresql.ENUM(name="payment_status").drop(op.get_bind(), checkfirst=True)
