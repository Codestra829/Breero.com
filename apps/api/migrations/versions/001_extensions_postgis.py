"""enable PostgreSQL extensions

Revision ID: 001_extensions_postgis
Revises:
Create Date: 2026-08-11
"""

from alembic import op

revision = "001_extensions_postgis"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    # Extensions may be shared with other schemas and own many PostGIS objects.
    # Deliberately retain them during application downgrade.
    pass
