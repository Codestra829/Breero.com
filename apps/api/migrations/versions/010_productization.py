"""catalog, public forms, and professional lead productization

Revision ID: 010_productization
Revises: 009_final_staging_boundaries
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "010_productization"
down_revision = "009_final_staging_boundaries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A disabled optional CRM is a durable, inspectable delivery state—not a
    # successful external delivery and not a retryable failure.
    op.execute("ALTER TYPE integration_event_status ADD VALUE IF NOT EXISTS 'PENDING_CONFIGURATION'")
    op.add_column("services", sa.Column("category", sa.String(100), nullable=False, server_default="home-services"))
    op.add_column("services", sa.Column("pricing_model", sa.String(32), nullable=False, server_default="quote_required"))
    op.add_column("services", sa.Column("is_bookable", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("services", "base_price", nullable=True)
    op.alter_column("services", "duration_minutes", nullable=True)
    op.create_index("ix_services_is_bookable", "services", ["is_bookable"])
    op.alter_column("services", "category", server_default=None)
    op.alter_column("services", "pricing_model", server_default=None)
    op.alter_column("services", "is_bookable", server_default=None)

    submission_type = postgresql.ENUM("SERVICE_REQUEST", "CONTACT", "PROVIDER_INTEREST", name="public_submission_type", create_type=False)
    downstream = postgresql.ENUM("PENDING", "PENDING_CONFIGURATION", "DELIVERED", "FAILED", name="public_submission_downstream_status", create_type=False)
    lead_status = postgresql.ENUM("AVAILABLE", "PURCHASED", "CLOSED", name="professional_lead_status", create_type=False)
    purchase_status = postgresql.ENUM("PENDING_PAYMENT", "PAID", "FAILED", "REFUNDED", name="lead_purchase_status", create_type=False)
    dispute_status = postgresql.ENUM("OPEN", "APPROVED", "DENIED", name="lead_dispute_status", create_type=False)
    for enum in (submission_type, downstream, lead_status, purchase_status, dispute_status):
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "public_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_type", submission_type, nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("normalized_email", sa.String(320), nullable=False),
        sa.Column("normalized_phone", sa.String(40)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("downstream_status", downstream, nullable=False),
        sa.Column("source_ip_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("submission_type", "idempotency_key", name="uq_public_submission_key"),
    )
    op.create_index("ix_public_submissions_submission_type", "public_submissions", ["submission_type"])
    op.create_index("ix_public_submissions_normalized_email", "public_submissions", ["normalized_email"])
    op.create_index("ix_public_submissions_normalized_phone", "public_submissions", ["normalized_phone"])

    op.create_table(
        "professional_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "service_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public_submissions.id", ondelete="SET NULL"),
            unique=True,
        ),
        sa.Column("service_category", sa.String(100), nullable=False),
        sa.Column("location_summary", sa.String(200), nullable=False),
        sa.Column("qualification_criteria", postgresql.JSONB(), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("policy_version", sa.String(40), nullable=False),
        sa.Column("status", lead_status, nullable=False),
        sa.Column("purchased_by_vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_professional_leads_service_category", "professional_leads", ["service_category"])
    op.create_index("ix_professional_leads_status", "professional_leads", ["status"])
    op.create_index("ix_professional_leads_purchased_by_vendor_id", "professional_leads", ["purchased_by_vendor_id"])
    op.create_table(
        "professional_lead_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("professional_leads.id"), nullable=False, unique=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", purchase_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vendor_id", "idempotency_key", name="uq_lead_purchase_key"),
    )
    op.create_index("ix_professional_lead_purchases_vendor_id", "professional_lead_purchases", ["vendor_id"])
    op.create_table(
        "professional_lead_disputes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("professional_lead_purchases.id"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("reason", sa.String(80), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("status", dispute_status, nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolution", sa.String(80)),
        sa.Column("resolution_reference", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("purchase_id", "reason", name="uq_lead_dispute_reason"),
    )
    op.create_index("ix_professional_lead_disputes_purchase_id", "professional_lead_disputes", ["purchase_id"])
    op.create_index("ix_professional_lead_disputes_vendor_id", "professional_lead_disputes", ["vendor_id"])


def downgrade() -> None:
    op.drop_table("professional_lead_disputes")
    op.drop_table("professional_lead_purchases")
    op.drop_table("professional_leads")
    op.drop_table("public_submissions")
    for name in ("lead_dispute_status", "lead_purchase_status", "professional_lead_status", "public_submission_downstream_status", "public_submission_type"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_services_is_bookable", table_name="services")
    op.drop_column("services", "is_bookable")
    op.drop_column("services", "pricing_model")
    op.drop_column("services", "category")
