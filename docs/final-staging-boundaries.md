# Final architecture and staging boundary evidence

Source SHA: `4954cc7c15ae566acda2e1ae768fbeaf87b1f3bf`  
Date: 2026-08-12

## Closed correctness boundaries

- Job completion, history, compensation snapshot, earning, and completion outbox event share one
  transaction. A forced post-earning failure rolls all of them back and a retry creates one earning.
- All application job status mutations use `JobService.apply_transition`; work requests use one
  explicit transition map. Operations rejection now records actor, reason, and job history.
- The zero-UUID payout compatibility alias was removed.
- Outbox claims carry an expiring lease and random claim token. Stale processing work is reclaimable;
  active leases remain exclusive. Delivery remains explicitly at-least-once with stable event IDs.
- Guest confirmation tokens are 256-bit opaque values, stored only as hashes, compared safely,
  scoped to one booking, expiring/revocable, and returned only at booking creation.
- Guest payment preparation derives amount, currency, and purpose from the locked booking. The
  browser Payment Element uses only the publishable Stripe key and polls the scoped backend state on
  a bounded schedule; client-side Stripe completion is never authoritative.

## Verified gates

- Backend Ruff and Mypy pass; 69 pytest tests pass against PostgreSQL/PostGIS.
- Fresh, 005, and 008 upgrades reach `009_final_staging_boundaries`; `alembic check` reports no drift.
- OpenAPI: 60 paths / 67 unique operations; frontend path and enum contract gate passes.
- Frontend lint, typecheck, 46 unit/package tests, and production build pass.
- Mock browser suite: 93 pass across Chromium, Firefox, and WebKit, including axe smoke checks.
- Runtime Docker image builds non-root; Trivy reports zero fixable HIGH/CRITICAL findings.

## Staging blockers

The required browser-to-live-API-to-database suite was not run. This host remains at 100% filesystem
usage and the mission explicitly prohibits creating another large isolated environment on an unsafe
host. No Stripe sandbox publishable/secret/webhook credentials were supplied. Consequently live
canonical payment, live browser auth/refresh/reset, browser two-customer isolation, and live
additional-work payment remain **BLOCKED**, not passed.

Decision: **NOT READY FOR STAGING**. Production remains **NO-GO**.
