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

The generated OpenAPI document at `/openapi.json` is the canonical frontend contract. Provider
credentials are optional for local catalog/booking development and required only when exercising
their adapters.
