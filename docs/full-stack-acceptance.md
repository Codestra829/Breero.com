# BREERO full-stack acceptance evidence

Date: 2026-08-12  
Branch: `codex/full-stack-acceptance-final`

## Integrated inputs

- Backend master: `da57218c73f2050ce1d6ed71f92bbeb737195527`
- Frontend master: `70b22c9b8d4b978c33fe8190f8b2fff956c56e88`
- Integration merges: `720644f` (frontend), `8fd87df` (backend)
- Alembic head: `008_production_readiness`
- OpenAPI: 58 paths / 65 operations, with unique operation IDs

## Contract corrections

The frontend types and rendering follow the generated backend contract for dynamic question types, `vendor_admin`, lowercase payment statuses, and `QUOTE_ADDITIONAL_WORK`. The guest booking UI does not poll the privileged operations payment endpoint. A redirect or client-side state is never treated as authoritative payment success. Account resource failures are now mapped to status-classed customer-safe text, so backend exception details are not rendered. Assignment, quote-decision, refund, compensation, payout, and manual integration-retry audit actions have explicit coverage.

## Validation evidence

- Frontend frozen install: pass
- Frontend lint and typecheck: pass
- Frontend unit/component tests: 36 pass
- Next.js production build: pass, 31 static/generated pages, 102 kB shared first-load JavaScript
- Chromium Playwright: 26 pass across 375, 430, 768, 1024, 1280, and 1440 px checks
- Backend Ruff: pass
- Backend Mypy: pass (83 source files)
- Backend pytest: 65 pass, including canonical lifecycle, negative lifecycle, and eight PostgreSQL concurrency cases
- Fresh PostgreSQL/PostGIS migration and production-like `005_booking_integrations -> head`: pass
- `alembic heads`, `current`, and `check`: one `008_production_readiness` head, current at head, no drift on both databases
- Runtime image Trivy HIGH/CRITICAL fixable scan: zero findings
- Runtime image: 94.2 MB, UID/GID 10001, 16.6 kB build context after Docker ignore hardening
- Local isolated API baseline (five requests, not an SLO): median 0.68 ms `/health`, 2.03 ms `/health/ready`, 1.30 ms `/openapi.json`
- Persisted canonical records: 3 linked customer lifecycles, 6 payments, 9 provider events, 3 jobs/assignments/work requests/earnings/payouts, 18 integration events, and 19 audit entries
- Existing shared Caddy configuration: valid (warnings only)

The current browser suite runs with the explicit test mock adapter. It validates UI behavior and responsive layout, but is not evidence of a browser-to-live-API canonical lifecycle. The backend canonical lifecycle test persists the full booking/payment/job/finance/outbox path with fake providers independently.

## Staging blockers

1. The frontend has no Stripe Elements/Checkout handoff and no owner-scoped guest confirmation contract. A guest can create a payment intent but cannot complete and observe authoritative confirmation through the browser.
2. Account pages use the mock adapter in browser tests; no browser test proves registration, verification, refresh rotation, two-customer ownership, quotes, refunds, or the account lifecycle against the isolated API.
3. There are no vendor, technician, operations, or finance browser applications/routes in the integrated frontend. Those lifecycle stages are backend-tested only.
4. Firefox/WebKit and automated axe checks were not configured; Chromium keyboard/landmark and responsive checks pass.
5. Production Compose requires an operator-supplied `.env.production`, immutable image digest, Redis secret, and shared-Caddy network name before complete config validation.

## Production blockers

- Root filesystem is now 100% used with approximately 1.5 GiB free. Cleanup must be reviewed, not blindly pruned.
- PostgreSQL 5432, Redis 6379, and API 8000 remain bound on all host interfaces.
- Shared Caddy owns 80/443. Its current full configuration validates; no BREERO route was changed.
- `breero.com` resolves to `13.248.243.5` / `76.223.105.230`, not this host; the BREERO API route/DNS cutover is not verified.
- Production provider credentials/configuration and production `.env.production` have not been supplied.
- No production backup/restore was performed during this read-only acceptance mission.

Result: **NOT READY FOR STAGING** for the requested browser-to-database canonical lifecycle, and **NO-GO FOR PRODUCTION**. Backend staging acceptance remains strong, while the customer payment and real-API browser boundary is incomplete.
