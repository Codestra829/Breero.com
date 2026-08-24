"""booking, serviceability, availability and durable integrations

Revision ID: 005_booking_integrations
Revises: 004_operations
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision = "005_booking_integrations"
down_revision = "004_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    booking_status = sa.Enum("PENDING_PAYMENT", "CONFIRMED", "CANCELLED", "EXPIRED", name="booking_status")
    event_status = sa.Enum("PENDING", "PROCESSING", "DELIVERED", "FAILED", name="integration_event_status")
    op.create_table("legal_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("service_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("legal_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("legal_entities.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("boundary", Geometry("MULTIPOLYGON", srid=4326), nullable=False), sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("formatted_address", sa.String(500), nullable=False), sa.Column("line1", sa.String(200), nullable=False),
        sa.Column("city", sa.String(120), nullable=False), sa.Column("postal_code", sa.String(32), nullable=False), sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("location", Geometry("POINT", srid=4326), nullable=False), sa.Column("service_area_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_areas.id")),
        sa.Column("geocoding_provider", sa.String(40)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("availability_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("service_area_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("service_areas.id"), nullable=False), sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False), sa.Column("end_time", sa.Time(), nullable=False), sa.Column("slot_minutes", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False), sa.Column("active_from", sa.Date()), sa.Column("active_to", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("first_name", sa.String(100), nullable=False), sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(320), nullable=False, index=True), sa.Column("phone", sa.String(40), nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("reference", sa.String(24), nullable=False, unique=True), sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False, index=True), sa.Column("address_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("addresses.id"), nullable=False),
        sa.Column("legal_entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("legal_entities.id"), nullable=False), sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False), sa.Column("window_end", sa.DateTime(timezone=True), nullable=False), sa.Column("status", booking_status, nullable=False),
        sa.Column("pricing_snapshot", postgresql.JSONB(), nullable=False), sa.Column("total_amount", sa.Numeric(12, 2), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("booking_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("value", sa.Text(), nullable=False))
    op.create_table("integration_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("aggregate_type", sa.String(80), nullable=False, index=True), sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("event_type", sa.String(120), nullable=False), sa.Column("payload", postgresql.JSONB(), nullable=False), sa.Column("status", event_status, nullable=False, index=True),
        sa.Column("attempts", sa.Integer(), nullable=False), sa.Column("available_at", sa.DateTime(timezone=True), nullable=False), sa.Column("delivered_at", sa.DateTime(timezone=True)), sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("actor_id", postgresql.UUID(as_uuid=True), index=True), sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False), sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade() -> None:
    for table in ("audit_logs", "integration_events", "booking_answers", "bookings", "customers", "availability_rules", "addresses", "service_areas", "legal_entities"):
        op.drop_table(table)
    sa.Enum(name="integration_event_status").drop(op.get_bind())
    sa.Enum(name="booking_status").drop(op.get_bind())
