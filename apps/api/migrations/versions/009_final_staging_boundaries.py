"""final staging transaction and ownership boundaries

Revision ID: 009_final_staging_boundaries
Revises: 008_production_readiness
"""

import sqlalchemy as sa
import secrets
import hashlib
from datetime import UTC, datetime, timedelta
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "009_final_staging_boundaries"
down_revision = "008_production_readiness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("guest_confirmation_token_hash", sa.String(64)))
    op.add_column(
        "bookings", sa.Column("guest_confirmation_expires_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "bookings", sa.Column("guest_confirmation_revoked_at", sa.DateTime(timezone=True))
    )
    connection = op.get_bind()
    for booking_id in connection.execute(sa.text("SELECT id FROM bookings")).scalars():
        token = secrets.token_urlsafe(32)
        connection.execute(
            sa.text(
                "UPDATE bookings SET guest_confirmation_token_hash=:token_hash, "
                "guest_confirmation_expires_at=:expires_at WHERE id=:booking_id"
            ),
            {
                "token_hash": hashlib.sha256(token.encode()).hexdigest(),
                "expires_at": datetime.now(UTC) + timedelta(hours=24),
                "booking_id": booking_id,
            },
        )
    op.alter_column("bookings", "guest_confirmation_token_hash", nullable=False)
    op.alter_column("bookings", "guest_confirmation_expires_at", nullable=False)
    op.add_column(
        "integration_events", sa.Column("lease_expires_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "integration_events", sa.Column("claim_token", postgresql.UUID(as_uuid=True))
    )
    op.create_index(
        "ix_integration_events_lease_expires_at", "integration_events", ["lease_expires_at"]
    )
    op.create_index("ix_integration_events_claim_token", "integration_events", ["claim_token"])
    op.add_column(
        "audit_logs",
        sa.Column("actor_type", sa.String(32), nullable=False, server_default="user"),
    )
    op.alter_column("audit_logs", "actor_type", server_default=None)


def downgrade() -> None:
    op.drop_column("bookings", "guest_confirmation_revoked_at")
    op.drop_column("bookings", "guest_confirmation_expires_at")
    op.drop_column("bookings", "guest_confirmation_token_hash")
    op.drop_column("audit_logs", "actor_type")
    op.drop_index("ix_integration_events_claim_token", table_name="integration_events")
    op.drop_index("ix_integration_events_lease_expires_at", table_name="integration_events")
    op.drop_column("integration_events", "claim_token")
    op.drop_column("integration_events", "lease_expires_at")
