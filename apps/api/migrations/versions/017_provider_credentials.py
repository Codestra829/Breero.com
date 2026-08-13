"""provider license and insurance verification records

Revision ID: 017_provider_credentials
Revises: 016_privacy_consent_controls
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "017_provider_credentials"
down_revision = "016_privacy_consent_controls"
branch_labels = None
depends_on = None


def upgrade():
    credential_type = postgresql.ENUM(
        "LICENSE", "INSURANCE", name="provider_credential_type", create_type=False
    )
    op.execute("CREATE TYPE provider_credential_type AS ENUM ('LICENSE','INSURANCE')")
    op.create_table(
        "provider_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("vendors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("credential_type", credential_type, nullable=False),
        sa.Column("jurisdiction", sa.String(3), nullable=False),
        sa.Column("reference_last4", sa.String(4)),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("expires_on", sa.Date, nullable=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("vendor_id", "credential_type", "jurisdiction"),
    )
    op.create_index("ix_provider_credentials_vendor_id", "provider_credentials", ["vendor_id"])
    op.create_index(
        "ix_provider_credentials_credential_type", "provider_credentials", ["credential_type"]
    )
    op.create_index(
        "ix_provider_credentials_jurisdiction", "provider_credentials", ["jurisdiction"]
    )
    op.create_index("ix_provider_credentials_expires_on", "provider_credentials", ["expires_on"])


def downgrade():
    op.drop_table("provider_credentials")
    postgresql.ENUM(name="provider_credential_type").drop(op.get_bind())
