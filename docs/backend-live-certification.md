# Backend live certification — 2026-08-12

## Passed evidence

- Source: Ruff, Mypy, 73 Pytest tests, PostgreSQL-backed acceptance, concurrency/negative tests.
- Migrations: fresh, 005, and 008 to the single `010_productization` head; `alembic check` clean.
- Security: Gitleaks clean; pip-audit clean after a patched pip; Trivy zero high/critical findings.
- Runtime: isolated PostGIS and Redis healthy; API live/ready 200; Celery worker ping succeeds.
- Contract: productized source has 70 paths, 77 operations, and 77 unique operation IDs at
  `/openapi.json`.
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
- Final customer boundaries: owner-scoped payment detail excludes the Stripe client secret;
  cancellation is audited, idempotent, revokes guest access, and hides cross-customer resources.
- Rollback: compatible prior API/worker image reached readiness, then the final 62-path image was
  restored without database migration or data loss.
- External staging API: on 2026-08-12 both Cloudflare (`1.1.1.1`) and Google (`8.8.8.8`) resolved
  `api-staging.breero.com` to `49.12.145.107`; its hostname-matched TLS certificate, live/ready,
  OpenAPI, and service-catalog requests passed over HTTPS.
- Product intake: the 12-service Texas launch taxonomy is active, legacy Berlin and certification
  fixtures are inactive, and Service Request, Contact, and Provider Interest each persisted through
  the live staging API with idempotent replay and transactional outbox creation.
- Live frontend: `staging.breero.com` serves the immutable `4485344` frontend over hostname-matched
  TLS in live API mode. Chromium, Firefox, and WebKit each submitted all three intake forms; the
  seven responsive widths from 375 through 1920 pixels passed without horizontal overflow.

## Blocked evidence

- Stripe test, email, SMS, geocoding, Odoo, and payout credentials were unavailable and are explicitly
  disabled. Signed webhook, sandbox payments/refunds, external geocoding, and provider UAT are blocked.
- Booking and paid-lead browser UAT remain blocked because launch services intentionally remain
  non-bookable until external geocoding and Stripe sandbox credentials are certified. The live
  booking screen loads all 12 authoritative services, disables unavailable choices, and offers the
  durable Service Request path instead of presenting fabricated availability.
- Production API activation is blocked until production-only credentials and a private production
  data plane are provisioned and the Stripe/browser gates pass. `api.breero.com` deliberately returns
  a TLS-valid `503` maintenance response rather than routing production users into staging.
- Paid professional opportunities now have provider-owned list/detail/purchase/dispute boundaries,
  but live purchase remains disabled until Stripe sandbox certification succeeds.

Production remains **NO-GO**.
