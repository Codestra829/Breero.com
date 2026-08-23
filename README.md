# BREERO

Home services. One booking.

BREERO is a multi-surface home-services marketplace and field-service orchestration platform.

## Marketplace V2 planning authority

The current production candidate remains request-only, manual-dispatch-first and payment-free. The V2 plan makes ProjectRequest the canonical demand model, with Matching, Opportunity, LeadConnection, Conversation, Quote, Booking, Job and Verified Review as distinct downstream stages.

Start with [the unified architecture](docs/architecture/MARKETPLACE_V2.md), [the system boundary](docs/architecture/system.md) and [the Codex master mission](docs/codex/MARKETPLACE_V2_MASTER_MISSION.md). Implementation must follow small sequential PRs from the current payment-free branch; this planning branch is not deployable.

Canonical identity issuer: https://auth.codestra.co/realms/codestra.

## Repository layout

- `apps/api` — FastAPI backend (PostgreSQL/PostGIS, SQLAlchemy async, Psycopg 3, Alembic, Redis)
- `apps/web` — public marketplace and customer portal
- `apps/partner` — vendor and technician portal
- `apps/ops` — BREERO operations and dispatch portal
- `apps/admin` — administration and finance portal
- `packages/ui` — shared frontend design system
- `packages/types` — shared frontend contracts
- `packages/api-client` — typed frontend API client
- `infrastructure` — deployment, proxy, backups and monitoring
- `docs` — architecture, API, security, operations and Codex workstream documentation

## Backend architecture

`API router -> domain service -> repository/query -> SQLAlchemy -> PostgreSQL`

The first production vertical slice is:

`address validation -> services/questions -> availability -> guest booking -> pricing snapshot`

The second vertical slice is:

`Stripe webhook -> payment captured -> booking confirmed -> job -> vendor matching -> ops`

## Development

Copy `.env.example` to `.env`, then run:

```bash
docker compose up --build
```

API health: `http://localhost:8000/health`

API docs: `http://localhost:8000/docs`

## Production target

Backend host: `49.12.145.107`

Production secrets are never committed to this repository.
