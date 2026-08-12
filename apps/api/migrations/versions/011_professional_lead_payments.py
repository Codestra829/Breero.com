"""connect professional lead purchases to canonical payments

Revision ID: 011_professional_lead_payments
Revises: 010_productization
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "011_professional_lead_payments"
down_revision = "010_productization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires newly added enum values to commit before they are used
    # in constraints or writes.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE professional_lead_status ADD VALUE IF NOT EXISTS 'RESERVED'")
        op.execute("ALTER TYPE payment_purpose ADD VALUE IF NOT EXISTS 'PROFESSIONAL_LEAD'")
    op.add_column(
        "payments",
        sa.Column(
            "lead_purchase_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professional_lead_purchases.id"),
        ),
    )
    op.create_index(
        "ix_payments_lead_purchase_id", "payments", ["lead_purchase_id"], unique=True
    )
    op.drop_constraint("valid_payment_reference", "payments", type_="check")
    op.create_check_constraint(
        "valid_payment_reference",
        "payments",
        "(payment_purpose = 'BOOKING_DIAGNOSTIC' AND booking_id IS NOT NULL AND quote_id IS NULL AND lead_purchase_id IS NULL) OR "
        "(payment_purpose = 'QUOTE_ADDITIONAL_WORK' AND booking_id IS NULL AND quote_id IS NOT NULL AND lead_purchase_id IS NULL) OR "
        "(payment_purpose = 'PROFESSIONAL_LEAD' AND booking_id IS NULL AND quote_id IS NULL AND lead_purchase_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("valid_payment_reference", "payments", type_="check")
    op.create_check_constraint(
        "valid_payment_reference",
        "payments",
        "(payment_purpose = 'BOOKING_DIAGNOSTIC' AND booking_id IS NOT NULL AND quote_id IS NULL) OR "
        "(payment_purpose = 'QUOTE_ADDITIONAL_WORK' AND booking_id IS NULL AND quote_id IS NOT NULL)",
    )
    op.drop_index("ix_payments_lead_purchase_id", table_name="payments")
    op.drop_column("payments", "lead_purchase_id")
    # PostgreSQL enum values are intentionally retained; removing values is unsafe
    # when rolling application code back and does not affect the prior schema.
