"""add users, roles, service catalog and dynamic questions

Revision ID: 002_auth_catalog
Revises: 001_extensions_postgis
Create Date: 2026-08-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002_auth_catalog"
down_revision = "001_extensions_postgis"
branch_labels = None
depends_on = None

user_role = postgresql.ENUM(
    "customer",
    "vendor_admin",
    "technician",
    "operations",
    "finance",
    "admin",
    name="user_role",
    create_type=False,
)
question_type = postgresql.ENUM(
    "text",
    "textarea",
    "number",
    "boolean",
    "single_choice",
    "multi_choice",
    name="question_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    question_type.create(bind, checkfirst=True)
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("role", user_role, server_default="customer", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "services",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_services_slug", "services", ["slug"], unique=True)
    op.create_index("ix_services_is_active", "services", ["is_active"])
    op.create_table(
        "service_questions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(240), nullable=False),
        sa.Column("help_text", sa.Text()),
        sa.Column("question_type", question_type, nullable=False),
        sa.Column("required", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("options", postgresql.JSONB()),
        sa.Column("validation", postgresql.JSONB()),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_id", "key", name="uq_service_questions_service_key"),
    )
    op.create_index("ix_service_questions_service_id", "service_questions", ["service_id"])


def downgrade() -> None:
    op.drop_table("service_questions")
    op.drop_table("services")
    op.drop_table("users")
    question_type.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
