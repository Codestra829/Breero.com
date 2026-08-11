"""merge auth/customer/payment and finance/integration histories

Revision ID: 007_backend_merge
Revises: 006_auth_customer_payments, 006_finance_integrations
"""

revision = "007_backend_merge"
down_revision = ("006_auth_customer_payments", "006_finance_integrations")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Both parent migrations own disjoint objects; no reconciliation DDL is required."""


def downgrade() -> None:
    """Downgrade from the merge point only separates the two intentional histories."""
