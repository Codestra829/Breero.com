# BREERO Marketplace V2 — Codex Master Mission

## Mission

Transform the current request-only BREERO application into a production-quality two-sided services marketplace and provider SaaS. Use the architecture documents in docs/architecture as the implementation authority.

ProjectRequest is customer demand. Booking is downstream. Job is execution. Review is verified trust.

## Base and branch discipline

- Planning authority base: codex/breero-production-without-payments at c48e5deb2880657396ce5a9eac51a35ff7ecfdde.
- Complete PR-00 release safety before V2 schema implementation.
- Create every implementation branch from the latest merged marketplace target.
- Keep PRs small, sequential and independently testable.
- Do not merge, deploy or activate external side effects unless the specific mission authorizes it.

## Non-negotiable current safety

Keep request-only/manual dispatch behavior. Keep payments, paid leads, payouts, automatic assignment, automatic confirmation, marketing, unrestricted email/SMS and external automation disabled.

## Required architecture

- Next.js multi-surface monorepo: public/customer, partner, operations and admin.
- FastAPI modular monolith with router → service → repository/query → async SQLAlchemy → PostgreSQL/PostGIS.
- Explicit domain commands and state transitions.
- Redis/Celery only for disposable state and workers.
- Transactional outbox and idempotent inbox.
- BREERO is marketplace source of truth.
- Canonical identity issuer is auth.codestra.co only.
- Codestra/Kong is the protected integration boundary; Odoo/n8n/email/SMS are downstream projections or executors.

## Execution order

Follow MIGRATION_PLAN_V2.md from PR-00 through PR-17. Do not start payments before ProjectRequest → matching → opportunity → connection → conversation → quote → booking → job → review works with payments disabled.

## Per-PR deliverables

- code and additive Alembic migration;
- OpenAPI and typed frontend contract updates;
- unit, PostgreSQL/PostGIS integration, authorization, negative, idempotency and relevant concurrency tests;
- frontend lint, typecheck, components, accessibility and responsive tests;
- operational metrics, safe logs, runbook and rollback note;
- exact files changed, commands run and unresolved risks.

## Completion

Marketplace MVP is complete only when the canonical end-to-end and every negative case in MARKETPLACE_V2_ACCEPTANCE_TESTS.md pass from the current production-compatible schema. A schema or UI shell alone is not completion.
