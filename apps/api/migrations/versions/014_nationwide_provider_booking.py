"""add fail-closed nationwide provider booking

Revision ID: 014_nationwide_provider_booking
Revises: 013_odoo_crm_delivery
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision = "014_nationwide_provider_booking"
down_revision = "013_odoo_crm_delivery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'PENDING_PROVIDER_CONFIRMATION'")
    op.alter_column("service_areas", "boundary", existing_type=Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    op.add_column("addresses", sa.Column("timezone_name", sa.String(64), nullable=False, server_default="UTC"))
    op.alter_column("addresses", "timezone_name", server_default=None)
    op.add_column("bookings", sa.Column("provider_worker_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key("fk_bookings_provider_worker_id_workers", "bookings", "workers", ["provider_worker_id"], ["id"])
    op.create_index("ix_bookings_provider_worker_id", "bookings", ["provider_worker_id"])
    op.create_table(
        "provider_service_coverage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("postal_code", sa.String(10), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("worker_id", "service_id", "postal_code"),
    )
    op.create_index("ix_provider_service_coverage_worker_id", "provider_service_coverage", ["worker_id"])
    op.create_index("ix_provider_service_coverage_service_id", "provider_service_coverage", ["service_id"])
    op.create_index("ix_provider_service_coverage_postal_code", "provider_service_coverage", ["postal_code"])
    op.create_table(
        "provider_working_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="provider_hours_weekday"),
        sa.CheckConstraint("capacity = 1", name="provider_hours_capacity_one"),
        sa.CheckConstraint("start_time = TIME '07:00:00'", name="provider_hours_start_policy"),
        sa.CheckConstraint("end_time = TIME '19:00:00'", name="provider_hours_end_policy"),
        sa.CheckConstraint("end_time > start_time", name="provider_hours_valid_range"),
        sa.UniqueConstraint("worker_id", "weekday"),
    )
    op.create_index("ix_provider_working_hours_worker_id", "provider_working_hours", ["worker_id"])


def downgrade() -> None:
    op.drop_table("provider_working_hours")
    op.drop_table("provider_service_coverage")
    op.drop_index("ix_bookings_provider_worker_id", table_name="bookings")
    op.drop_constraint("fk_bookings_provider_worker_id_workers", "bookings", type_="foreignkey")
    op.drop_column("bookings", "provider_worker_id")
    op.drop_column("addresses", "timezone_name")
    op.alter_column("service_areas", "boundary", existing_type=Geometry("MULTIPOLYGON", srid=4326), nullable=False)
    # PostgreSQL enum value removal is intentionally not attempted.
