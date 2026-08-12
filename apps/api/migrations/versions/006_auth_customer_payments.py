"""production auth, customer ownership, quote payments and refunds

Revision ID: 006_auth_customer_payments
Revises: 005_booking_integrations
"""

from alembic import op

revision = "006_auth_customer_payments"
down_revision = "005_booking_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN email_verified boolean NOT NULL DEFAULT false")
    op.execute("ALTER TABLE users ADD COLUMN credential_version integer NOT NULL DEFAULT 1")
    op.execute("""
      CREATE TABLE auth_sessions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash varchar(64) NOT NULL UNIQUE, family_id uuid NOT NULL, user_agent varchar(500), ip_address varchar(64),
        expires_at timestamptz NOT NULL, rotated_at timestamptz, revoked_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
      ); CREATE INDEX ix_auth_sessions_user_id ON auth_sessions(user_id); CREATE INDEX ix_auth_sessions_token_hash ON auth_sessions(token_hash);
      CREATE INDEX ix_auth_sessions_family_id ON auth_sessions(family_id); CREATE INDEX ix_auth_sessions_expires_at ON auth_sessions(expires_at)
    """)
    for table in ("password_reset_tokens", "email_verification_tokens"):
        op.execute(f"""
          CREATE TABLE {table} (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash varchar(64) NOT NULL UNIQUE, expires_at timestamptz NOT NULL, used_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now()
          ); CREATE INDEX ix_{table}_user_id ON {table}(user_id); CREATE INDEX ix_{table}_token_hash ON {table}(token_hash)
        """)
    op.execute("ALTER TABLE customers ADD CONSTRAINT fk_customers_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE addresses ADD COLUMN customer_id uuid REFERENCES customers(id) ON DELETE CASCADE")
    op.execute("CREATE INDEX ix_addresses_customer_id ON addresses(customer_id)")
    op.execute("ALTER TYPE work_request_status ADD VALUE IF NOT EXISTS 'PENDING_CUSTOMER'")
    op.execute("ALTER TYPE work_request_status ADD VALUE IF NOT EXISTS 'APPROVED_PENDING_PAYMENT'")
    op.execute("ALTER TYPE work_request_status ADD VALUE IF NOT EXISTS 'EXPIRED'")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'partially_refunded'")
    op.execute("CREATE TYPE payment_purpose AS ENUM ('BOOKING_DIAGNOSTIC','QUOTE_ADDITIONAL_WORK')")
    op.execute("ALTER TABLE payments ALTER COLUMN booking_id DROP NOT NULL")
    op.execute("ALTER TABLE payments ADD COLUMN quote_id uuid")
    op.execute("ALTER TABLE payments ADD COLUMN payment_purpose payment_purpose NOT NULL DEFAULT 'BOOKING_DIAGNOSTIC'")
    op.execute("CREATE INDEX ix_payments_quote_id ON payments(quote_id)")
    op.execute("ALTER TABLE payments ADD CONSTRAINT ck_payments_valid_payment_reference CHECK ((payment_purpose = 'BOOKING_DIAGNOSTIC' AND booking_id IS NOT NULL AND quote_id IS NULL) OR (payment_purpose = 'QUOTE_ADDITIONAL_WORK' AND booking_id IS NULL AND quote_id IS NOT NULL))")
    op.execute("ALTER TABLE payment_events ALTER COLUMN processed_at DROP NOT NULL")
    op.execute("ALTER TABLE payment_events ALTER COLUMN processed_at DROP DEFAULT")
    op.execute("ALTER TABLE payment_events ADD COLUMN status varchar(20) NOT NULL DEFAULT 'processing'")
    op.execute("ALTER TABLE payment_events ADD COLUMN attempts integer NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE payment_events ADD COLUMN last_error text")
    op.execute("UPDATE payment_events SET status='processed'")
    op.execute("CREATE TYPE refund_status AS ENUM ('pending','succeeded','failed','canceled')")
    op.execute("""
      CREATE TABLE refunds (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), payment_id uuid NOT NULL REFERENCES payments(id), amount_minor integer NOT NULL CHECK(amount_minor > 0),
        status refund_status NOT NULL, provider_refund_id varchar(255) UNIQUE, idempotency_key varchar(255) NOT NULL,
        reason varchar(500), created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT uq_refunds_payment_key UNIQUE(payment_id,idempotency_key)
      ); CREATE INDEX ix_refunds_payment_id ON refunds(payment_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE refunds")
    op.execute("DROP TYPE refund_status")
    op.execute("ALTER TABLE payment_events DROP COLUMN last_error, DROP COLUMN attempts, DROP COLUMN status")
    op.execute("ALTER TABLE payments DROP CONSTRAINT ck_payments_valid_payment_reference")
    op.execute("DROP INDEX ix_payments_quote_id")
    op.execute("ALTER TABLE payments DROP COLUMN payment_purpose, DROP COLUMN quote_id")
    op.execute("ALTER TABLE payments ALTER COLUMN booking_id SET NOT NULL")
    op.execute("DROP TYPE payment_purpose")
    op.execute("DROP INDEX ix_addresses_customer_id")
    op.execute("ALTER TABLE addresses DROP COLUMN customer_id")
    op.execute("ALTER TABLE customers DROP CONSTRAINT fk_customers_user_id_users")
    op.execute("DROP TABLE email_verification_tokens, password_reset_tokens, auth_sessions")
    op.execute("ALTER TABLE users DROP COLUMN credential_version, DROP COLUMN email_verified")
