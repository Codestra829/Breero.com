# BREERO Codex Master Brief

## Marketplace V2 authority

The following documents are authoritative for new marketplace work:

- ../architecture/MARKETPLACE_V2.md
- ../architecture/DOMAIN_MODEL_V2.md
- ../architecture/DATA_MODEL_V2.md
- ../architecture/API_V2.md
- ../architecture/EVENT_CATALOG_V2.md
- ../architecture/MATCHING_ENGINE_V2.md
- ../architecture/SYNC_INTEGRATIONS_V2.md
- ../architecture/SECURITY_RBAC_V2.md
- ../architecture/UX_DESIGN_V2.md
- ../architecture/PROVIDER_SAAS_V2.md
- ../architecture/OPS_COMMAND_CENTER_V2.md
- ../architecture/MIGRATION_PLAN_V2.md
- ../architecture/OBSERVABILITY_V2.md
- ../architecture/AZURE_TARGET_V2.md
- MARKETPLACE_V2_MASTER_MISSION.md
- MARKETPLACE_V2_IMPLEMENTATION_RULES.md
- MARKETPLACE_V2_ACCEPTANCE_TESTS.md

ProjectRequest is the canonical demand aggregate. Booking is downstream from an accepted marketplace outcome. Job is field execution. Verified Review requires a completed BREERO job.

## Current release boundary

The inspected base is codex/breero-production-without-payments at c48e5deb2880657396ce5a9eac51a35ff7ecfdde. Preserve request-only manual dispatch. Keep payments, paid leads, payouts, automatic assignment, automatic confirmation, marketing, unrestricted email/SMS and external automation disabled.

PR-00 release safety must complete before new Marketplace V2 schema. The planning branch is documentation-only and must never be deployed.

## Shared engineering rules

1. Inspect current architecture, migrations, OpenAPI and shared types before coding.
2. Use router → service → repository/query → async SQLAlchemy → PostgreSQL/PostGIS.
3. Use explicit domain commands and state transitions, never arbitrary status mutation.
4. State, history, audit and outbox commit in one transaction.
5. Keep persistence models separate from API schemas.
6. Use the actual Alembic head and additive migrations.
7. Require server-side permission, tenant scope and negative authorization tests.
8. Use auth.codestra.co only for the canonical issuer.
9. Preserve /api/v1 while /api/v2 is introduced.
10. Regenerate OpenAPI and typed clients together.
11. Redis, search, Odoo and n8n are not sources of marketplace truth.
12. No secret, production credential or customer document enters source or logs.
13. Run lint, typecheck, unit, PostgreSQL/PostGIS integration, migration, idempotency, concurrency and E2E tests relevant to the PR.
14. Keep PRs small and sequential; do not create a permanent V2 mega-branch.
15. Document exact baseline/final SHA, migration head, tests, risks and rollback.

## First complete vertical slice

ProjectRequest → qualification → matching → Opportunity → LeadConnection → Conversation → Quote → Booking → Job → Verified Review.

Prove zero-provider, expired-credential, cross-tenant, duplicate-command, expired-hold, integration-failure and payment-disabled cases.

## Delivery order

Follow ../architecture/MIGRATION_PLAN_V2.md. Payments, provider subscriptions and Azure modernization are phases 15–17, after the payment-free marketplace lifecycle is stable.

## Definition of done

Marketplace V2 is not complete because tables, routes or shells exist. It is complete only when MARKETPLACE_V2_ACCEPTANCE_TESTS.md passes from the current production-compatible schema, runtime capabilities accurately control backend and UI, integrations reconcile, and no disabled feature is advertised or executed.

## Previous brief

The pre-V2 brief below is retained as historical context only. Where it conflicts with the V2 authority above, V2 wins.

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
CI/CD, Docker production configuration, reverse proxy, TLS, migrations, deployment to 49.12.145.107, backups, monitoring and health checks.

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
