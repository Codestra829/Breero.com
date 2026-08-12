# Backend live certification — 2026-08-12

## Passed evidence

- Source: Ruff, Mypy, 71 Pytest tests, PostgreSQL-backed acceptance, concurrency/negative tests.
- Migrations: fresh, 005, and 008 to the single 009 head; `alembic check` clean.
- Security: Gitleaks clean; pip-audit clean after a patched pip; Trivy zero high/critical findings.
- Runtime: isolated PostGIS and Redis healthy; API live/ready 200; Celery worker ping succeeds.
- Contract: 60 paths, 67 operations, 67 unique operation IDs at `/openapi.json`.
- CORS: exact staging origin accepted; unapproved origin rejected.
- Auth: register, duplicate conflict, login failure/success, verification, refresh rotation/reuse
  rejection, logout semantics, password reset, and old-password rejection.
- Catalog/address/availability: live database catalog and questions, coordinate-backed supported and
  unsupported addresses, invalid input rejection, and live availability.
- Booking: create, identical idempotent replay, mismatched-payload conflict, owner read, and
  cross-customer privacy-preserving 404.
- Resilience: staging Redis, API, and worker restart independently; readiness and persisted booking
  count recover.
- Outbox: real processing increments attempts without losing records; pre-expiry reclaim is denied
  and post-expiry stale lease reclaim succeeds.
- Backup: custom archive restored to a separate database at migration 009 with representative row
  counts matching.

## Blocked evidence

- `api-staging.breero.com` still resolves to incorrect target `49.12.145.207`; no DNS administrator
  credential was available. TLS and external API proof cannot pass until the A record is corrected.
- Stripe test, email, SMS, geocoding, Odoo, and payout credentials were unavailable and are explicitly
  disabled. Signed webhook, sandbox payments/refunds, external geocoding, and provider UAT are blocked.
- `staging.breero.com` also resolves to `.207`, so browser-to-live-API and cross-browser live UAT are
  blocked.
- The canonical contract has no professional-lead, lead-dispute, or customer-cancellation endpoints.

Production remains **NO-GO**.

