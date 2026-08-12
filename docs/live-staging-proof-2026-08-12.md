# BREERO live staging proof — 2026-08-12

## Decision

**NOT READY — UAT INCOMPLETE — NO SAFE STAGING COMPUTE**

No production mutation or staging deployment was performed. The only configured Docker context is
the local production host, whose root filesystem was previously verified at 100% with publicly
published BREERO database, Redis, and API ports. It cannot satisfy isolation requirements.

`staging.breero.com` resolves to `49.12.145.207`, but connection probes to 22, 80, 443, 5432,
6379, and 8000 were closed, filtered, or timed out. HTTPS and SSH were unavailable. There is no
authenticated alternative Docker/Kubernetes/SSH context and `staging-api.breero.com` has no address
record. Consequently the hostname cannot currently host or prove the requested environment.

## Candidate verification

| Item | Verified value |
|---|---|
| Source branch | `codex/final-architecture-staging-fixes` |
| Source / PR #22 head | `337e8e9ef47378643d221fb6c97d4ebdfe69e342` |
| PR #22 | open draft, mergeable, checks green |
| Alembic head | `009_final_staging_boundaries` (one head) |
| OpenAPI | 60 paths / 67 operations |
| Backend CI | 69 tests; focused PostgreSQL acceptance 15; Ruff/Mypy green |
| Frontend tests | 46 package/unit tests |
| Browser CI | 93 mock Playwright tests across Chromium, Firefox and WebKit |

Code inspection confirms atomic completion transaction ownership, centralized job/work-request
transitions, outbox claim leases, hashed guest confirmation credentials, server-derived guest
payment preparation, Stripe Payment Element integration, migration 009, current OpenAPI schemas,
three browser projects, and axe smoke coverage. No claimed fix was absent.

## Configuration and secrets

No staging secrets were available or created. No values were printed or committed. Stripe, Odoo,
email, SMS, geocoding, payout, JWT, database and Redis status is **MISSING/UNVERIFIED** for a live
staging deployment. Optional-provider fake/test selection therefore cannot be demonstrated as an
explicit deployed configuration.

## Gate results

Repository CI is green for the exact source SHA, but it does not prove a live environment. The
following mandatory gates are BLOCKED and must not be converted to PASS:

- isolated frontend/API/worker/scheduler/PostGIS/Redis deployment;
- HTTPS, CORS, cookie and frontend-to-API validation;
- Stripe test Payment Element, signed webhook, duplicate/failure/refund paths;
- real browser guest booking and authoritative confirmation;
- live auth, refresh rotation and password reset;
- two-customer, two-vendor and two-technician isolation;
- quote/additional payment, finance and payout sandbox flow;
- live completion fault injection and stale outbox lease recovery;
- live Chromium/Firefox/WebKit/mobile/accessibility UAT;
- Redis-backed rate limits, workers, observability, performance and controlled load;
- post-UAT database integrity, custom backup/isolated restore, and rollback rehearsal;
- live `/openapi.json` comparison.

## Required unblock

Provide an approved isolated compute target with DNS/TLS and non-production secrets, or an
authenticated private access path to `49.12.145.207` after its ownership/capacity is confirmed.
PostgreSQL and Redis must remain private. Stripe keys must be test-mode and account-compatible; all
other providers must be explicitly sandbox-enabled or fake/disabled. Only then can live UAT begin.

Production remains **NO-GO** independently of this staging block.
