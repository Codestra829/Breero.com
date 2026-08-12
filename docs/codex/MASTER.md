# BREERO Codex Master Brief

## Mission

Build BREERO as a production-quality home-services marketplace and field-service orchestration platform. Keep frontend, backend, operations, partner and finance concerns explicit and independently maintainable.

## Shared rules

1. Inspect existing architecture, shared types, migrations and domain services before coding.
2. Stay within the assigned workstream; do not redesign unrelated modules.
3. Never commit secrets or production credentials.
4. Backend flow is `router -> service -> repository/query -> SQLAlchemy -> PostgreSQL`.
5. Keep SQLAlchemy models separate from Pydantic request/response schemas.
6. Use Alembic for every database schema change. Never use `Base.metadata.create_all()` as production schema management.
7. Use explicit domain commands/state transitions instead of arbitrary status mutation.
8. Run formatting, linting, type checking and relevant tests before completion.
9. Document API dependencies and TODOs in the PR summary.
10. Avoid giant commits and unrelated changes.

## Backend vertical slice 1

Implement end-to-end before expanding horizontally:

`POST /api/v1/addresses/validate`
-> `GET /api/v1/services`
-> `GET /api/v1/services/{id}/questions`
-> `POST /api/v1/availability/search`
-> `POST /api/v1/bookings`
-> guest customer
-> booking
-> immutable pricing snapshot
-> payment requirement

## Backend vertical slice 2

Stripe checkout/payment -> verified/idempotent webhook -> payment CAPTURED -> booking CONFIRMED -> job created -> vendor matching -> operations visibility.

## Workstreams

### codex/backend-foundation
FastAPI, SQLAlchemy async, Psycopg 3, Alembic, PostGIS, Redis, configuration, Docker, health, logging, common errors and tests.

### codex/booking-core
Legal entities, addresses, service areas, services, dynamic questions, scheduling, availability, customers, bookings and pricing snapshots.

### codex/payments
Stripe adapter, payment records, provider events, webhook verification/idempotency, refunds foundation.

### codex/dispatch-matching
Vendors, workers, coverage, qualifications, job creation/state, matching runs/candidates, offers and assignments.

### codex/frontend-public
Public marketplace, service pages, booking wizard, checkout, confirmation and customer portal foundations.

### codex/partner-portal
Vendor offers, jobs, worker assignment, technician commands, evidence/diagnostics, work requests, earnings and payouts views.

### codex/ops-admin
Dispatch board, jobs, matching, quotes, vendors, exceptions, service configuration, finance/admin surfaces.

### codex/devops
CI/CD, Docker production configuration, reverse proxy, TLS, migrations, deployment planning for the current host 49.12.145.107, backups, monitoring and health checks.

## Core state rules

Job transitions are controlled centrally (e.g. `JobStateService.transition`). Completion must validate assignment, required evidence, notes and diagnostic data. State update + history + integration event + audit log belong in one transaction.

## Finance rules

Customer pricing and vendor compensation are separate models. Dispatcher users must receive 403 for payout approval/submission. Finance and super-admin permissions are explicit and server-enforced.

## Integration rules

Stripe, Odoo, email, SMS and geocoding live behind adapters. Business services do not contain provider-specific HTTP code. Odoo synchronization uses durable integration events/outbox processing.

## Definition of done for milestone 1

- Docker stack starts API, PostGIS and Redis.
- Alembic applies cleanly to an empty database.
- `/health`, `/health/live`, `/health/ready` work.
- Seed data provides one legal entity, service area, service, questions and availability configuration.
- Address validation resolves serviceability/legal entity.
- Services/questions, availability and guest booking work end-to-end.
- Pricing snapshot is persisted.
- Business logic is outside routes.
- Tests cover success plus invalid service area, unavailable slot and core retry/concurrency behavior.
- README explains startup.
- No secrets are committed.

## BREERO FRONTEND — MASTER FINAL EXECUTION MISSION

Branch: `codex/frontend-master-final`

Integrate and reconcile these completed frontend workstreams without starting a new architecture from scratch:

- `codex/frontend-system-90`
- `codex/frontend-booking-90`
- `codex/frontend-customer-90`
- `codex/frontend-integration-90`

Preserve strong completed work, resolve conflicts deliberately, and produce one coherent frontend implementation. Backend/OpenAPI is authoritative. The primary target is approximately 90% staging-ready frontend completion.

Execution priorities:

1. Integrate the four frontend workstreams.
2. Reconcile `packages/ui`.
3. Reconcile `packages/api-client` and `packages/types`.
4. Replace stale mocks with live backend contracts.
5. Complete homepage and service discovery.
6. Complete the booking flow.
7. Complete authentication UX.
8. Complete the customer portal.
9. Complete quote and additional-payment UX.
10. Complete loading, empty, error, and session states.
11. Complete responsive behavior.
12. Complete accessibility fundamentals.
13. Run full lint, typecheck, tests, and production build.
14. Run canonical and negative end-to-end tests.
15. Deliver a precise staging-readiness report.

Do not merge this branch. Push only to `codex/frontend-master-final`.
