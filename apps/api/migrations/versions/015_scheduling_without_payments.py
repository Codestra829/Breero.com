"""add request-only scheduling states

Revision ID: 015_scheduling_without_payments
Revises: 014_nationwide_provider_booking
"""
from alembic import op

revision = "015_scheduling_without_payments"
down_revision = "014_nationwide_provider_booking"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'REQUESTED'")
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'PENDING_MANUAL_DISPATCH'")
    op.execute("ALTER TYPE booking_status ADD VALUE IF NOT EXISTS 'TENTATIVE_HOLD'")

def downgrade() -> None:
    # PostgreSQL enum values are retained intentionally for rollback safety.
    pass
