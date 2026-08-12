# BREERO System Architecture

## Surfaces

- `breero.com` — public marketplace + customer account
- `partners.breero.com` — vendor/technician portal
- `ops.breero.com` — dispatch and operations
- `admin.breero.com` — admin and finance
- `api.breero.com/api/v1` — FastAPI backend

## Backend stack

FastAPI + PostgreSQL/PostGIS + SQLAlchemy async + Psycopg 3 + Alembic + Redis + Celery.

## Required layering

`router -> service -> repository/query -> SQLAlchemy -> PostgreSQL`

Pydantic API contracts are separate from SQLAlchemy persistence models.

## Core domains

Auth, users, customers, addresses, legal entities, service areas, services/questions, scheduling, bookings, vendors/workers, jobs, matching, dispatch, pricing, quotes, payments, earnings, payouts, notifications, audit and integrations.

## Transactional source of truth

BREERO PostgreSQL is the operational source of truth. Odoo is synchronized asynchronously through integration events/outbox processing.

## Payment truth

Stripe webhook events, after signature and idempotency verification, are authoritative for payment completion. Browser redirects are never authoritative.

## State control

Bookings and jobs use explicit domain transitions. Partner users receive command endpoints such as `/jobs/{id}/complete`, never unrestricted status patching.

## Security

Server-side RBAC/permissions, audit logging, webhook verification, idempotency, secret isolation, secure headers, CORS policy and rate limiting are required.

## Production

Current BREERO host: `49.12.145.107`. DNS currently resolves configured BREERO names to
`49.12.145.207`; that mismatch does not establish `.207` as a BREERO-owned origin.

Production topology: reverse proxy/TLS -> API -> PostgreSQL/PostGIS + Redis + workers/scheduler. Frontends remain independently deployable.
