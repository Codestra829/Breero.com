# BREERO API

FastAPI backend for BREERO.

## Stack

FastAPI, PostgreSQL/PostGIS, SQLAlchemy async, Psycopg 3, Alembic, Redis and Celery.

## Architecture rule

`API router -> service -> repository/query -> SQLAlchemy -> PostgreSQL`

Do not place substantial business logic in route handlers.

## Local development

From repository root:

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`
Health: `http://localhost:8000/health`

Apply migrations and load deterministic development data with:

```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.seed
```

## First vertical slice

1. `POST /api/v1/addresses/validate`
2. `GET /api/v1/services`
3. `GET /api/v1/services/{id}/questions`
4. `POST /api/v1/availability/search`
5. `POST /api/v1/bookings`

## Implemented domains

- JWT authentication and server-side customer, vendor, technician, operations, finance and admin RBAC
- catalog, dynamic questions, PostGIS service areas, availability and guest booking
- Stripe payment intents, verified/idempotent webhooks and booking-to-job creation
- vendors, workers, matching, offers, assignments and controlled job transitions
- technician diagnostics, additional-work quotes, customer decisions and completion evidence
- vendor earnings, finance-only payout batches and approval
- Celery expiry/outbox workers plus a retryable Odoo JSON-RPC adapter

## Authentication and customer accounts

Authentication under `/api/v1/auth` supports registration/login, rotating opaque refresh tokens,
single-session and all-session logout, password reset/change, and email verification. Refresh,
reset, and verification secrets are stored only as SHA-256 hashes. Password changes increment a
credential version, invalidating existing access tokens, and revoke every refresh session.

Guest customer history is linked to an account only after verification of the same normalized email.
Customer-owned profile, address, booking, quote, and payment endpoints live under
`/api/v1/customer`; collection endpoints use `page` and `page_size`.

Additional-work quote states are `SUBMITTED` (operations review), `PENDING_CUSTOMER`,
`APPROVED_PENDING_PAYMENT`, and `APPROVED`. Customer approval never authorizes the job to resume;
only a verified captured-payment webhook settles the quote and resumes work. Payments have an
explicit `BOOKING_DIAGNOSTIC` or `QUOTE_ADDITIONAL_WORK` purpose. Finance/admin users may create
full or partial refunds with an `Idempotency-Key`.

Auth notification events (`email_verification_requested`, `password_reset_requested`, and
`password_changed`) and financial events (`payment_captured`, `refund_created`) are written to the
existing integration outbox. Local tests may inspect this outbox; production delivery requires a
configured email worker. Stripe operations require `STRIPE_SECRET_KEY` and
`STRIPE_WEBHOOK_SECRET`. Production email delivery uses `EMAIL_DELIVERY_URL` and optional
`EMAIL_DELIVERY_API_KEY`; without a URL, non-production environments use the structured-log local
adapter.

The generated OpenAPI document at `/openapi.json` is the canonical frontend contract. Provider
credentials are optional for local catalog/booking development and required only when exercising
their adapters.
