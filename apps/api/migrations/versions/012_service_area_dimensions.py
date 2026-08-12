"""add reusable service area dimensions

Revision ID: 012_service_area_dimensions
Revises: 011_professional_lead_payments
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision = "012_service_area_dimensions"
down_revision = "011_professional_lead_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("service_areas", sa.Column("country_code", sa.String(2)))
    op.add_column("service_areas", sa.Column("state_code", sa.String(3)))
    op.add_column("service_areas", sa.Column("city", sa.String(120)))
    op.add_column(
        "service_areas",
        sa.Column("postal_codes", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column("service_areas", sa.Column("center", Geometry("POINT", srid=4326)))
    op.add_column("service_areas", sa.Column("radius_meters", sa.Integer()))
    op.create_index("ix_service_areas_country_code", "service_areas", ["country_code"])
    op.create_index("ix_service_areas_state_code", "service_areas", ["state_code"])
    op.create_index("ix_service_areas_city", "service_areas", ["city"])
    op.create_check_constraint(
        "service_area_radius_requires_center",
        "service_areas",
        "radius_meters IS NULL OR (radius_meters > 0 AND center IS NOT NULL)",
    )
    op.alter_column("service_areas", "postal_codes", server_default=None)
    op.add_column("addresses", sa.Column("state_code", sa.String(3)))


def downgrade() -> None:
    op.drop_column("addresses", "state_code")
    op.drop_constraint("service_area_radius_requires_center", "service_areas", type_="check")
    op.drop_index("ix_service_areas_city", table_name="service_areas")
    op.drop_index("ix_service_areas_state_code", table_name="service_areas")
    op.drop_index("ix_service_areas_country_code", table_name="service_areas")
    op.drop_column("service_areas", "radius_meters")
    op.drop_column("service_areas", "center")
    op.drop_column("service_areas", "postal_codes")
    op.drop_column("service_areas", "city")
    op.drop_column("service_areas", "state_code")
    op.drop_column("service_areas", "country_code")
