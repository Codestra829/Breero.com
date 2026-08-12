# BREERO full-stack acceptance evidence

Date: 2026-08-12  
Branch: `codex/full-stack-acceptance-final`

## Integrated inputs

- Backend master: `9a94a82c5ef815191409bf8e462b9fa8fd5b1bee`
- Frontend master: `cbc85f8e3f6630d712a7265e030e5eca7cdbf1f1`
- Integration merge: `fc1fdba`
- Alembic head: `008_production_readiness`
- OpenAPI: 58 paths / 65 operations, with unique operation IDs

## Contract corrections

The frontend types and rendering now follow the generated backend contract for dynamic question types, `vendor_admin`, lowercase payment statuses, and `QUOTE_ADDITIONAL_WORK`. The guest booking UI no longer polls the privileged operations payment endpoint. A redirect or client-side state is never treated as authoritative payment success.

## Validation evidence

- Frontend frozen install: pass
- Frontend lint and typecheck: pass
- Frontend unit/component tests: 35 pass
- Next.js production build: pass, 31 static/generated pages, 102 kB shared first-load JavaScript
- Chromium Playwright: 26 pass across 375, 430, 768, 1024, 1280, and 1440 px checks
- Backend Ruff: pass
- Backend Mypy: pass (83 source files)
- Backend pytest: 64 pass, including canonical lifecycle, negative lifecycle, and PostgreSQL concurrency cases
- Fresh PostgreSQL/PostGIS migration: pass
- `alembic heads`, `current`, and `check`: one head, current at head, no drift
- Runtime image Trivy HIGH/CRITICAL fixable scan: zero findings
- Existing shared Caddy configuration: valid (warnings only)

The current browser suite runs with the explicit test mock adapter. It validates UI behavior and responsive layout, but is not evidence of a browser-to-live-API canonical lifecycle. The backend canonical lifecycle test persists the full booking/payment/job/finance/outbox path with fake providers independently.

## Staging blockers

1. The frontend has no Stripe Elements/Checkout handoff and no owner-scoped guest confirmation contract. A guest can create a payment intent but cannot complete and observe authoritative confirmation through the browser.
2. Account pages use the mock adapter in browser tests; no browser test proves registration, verification, refresh rotation, two-customer ownership, quotes, refunds, or the account lifecycle against the isolated API.
3. There are no vendor, technician, operations, or finance browser applications/routes in the integrated frontend. Those lifecycle stages are backend-tested only.
4. Firefox/WebKit and automated axe checks were not configured; Chromium keyboard/landmark and responsive checks pass.
5. Production Compose requires an operator-supplied `.env.production`, immutable image digest, Redis secret, and shared-Caddy network name before complete config validation.

## Production blockers

- Root filesystem is 99% used with approximately 5.6 GiB free. Docker reports 339.9 GiB of images and 54.2 GiB of build cache; cleanup must be reviewed, not blindly pruned.
- PostgreSQL 5432, Redis 6379, and API 8000 remain bound on all host interfaces.
- Shared Caddy owns 80/443. Its current full configuration validates; no BREERO route was changed.
- `api.breero.com` does not currently resolve from the host.
- Production provider credentials/configuration and production `.env.production` have not been supplied.
- No production backup/restore was performed during this read-only acceptance mission.

Result: **NOT READY FOR STAGING** for the requested browser-to-database canonical lifecycle, and **NO-GO FOR PRODUCTION**. Backend staging acceptance remains strong, while the customer payment and real-API browser boundary is incomplete.
