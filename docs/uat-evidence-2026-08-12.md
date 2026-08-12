# Release evidence — 2026-08-12 12:22 UTC

## Source baseline

- Backend master: `da57218c73f2050ce1d6ed71f92bbeb737195527`.
- Frontend master: `70b22c9b8d4b978c33fe8190f8b2fff956c56e88`.
- Full-stack acceptance input: `253a597fa8261de897e4fe5fb837f3d9d4030f1f`.
- Migration head: `008_production_readiness`.
- OpenAPI: 58 paths / 65 operations; 25 frontend-required paths verified.
- Frontend build: 31 route entries.

## Isolated integration evidence

`breero-backend-audit-pg` and `breero-backend-audit-redis` are isolated on
`breero-backend-audit-net` with no published host ports. PostgreSQL reports head
`008_production_readiness`, 37 public tables, PostGIS and pgcrypto, plus the expected booking,
availability, assignment, payment, payout, outbox, and spatial indexes.

Current source was mounted read-only into a pre-existing test-tool image:

- Backend full suite: 65 passed in 2.51 seconds.
- Canonical, negative, and real PostgreSQL concurrency subset: 13 passed in 1.99 seconds.
- Covered booking capacity, webhook idempotency, assignment/job transition, outbox claiming,
  and duplicate payout submission races.

This is integration acceptance, not formal UAT. Test data covers three bookings, jobs, vendors,
and workers, but does not provide all seven login personas.

## Backup/restore rehearsal

- Archive: `/root/backups/breero-staging-uat-20260812T122000Z/breero-audit.dump`.
- Timestamp: `2026-08-12 12:19:38 UTC`; size: 127,515 bytes.
- SHA-256: `deb1589e8875974ba1afe8e192c4009e47cc61f52bf7fee4119fd767e99c6479`.
- Archive listing: passed. Restore target: isolated `breero_restore_uat` database.
- Restored head/tables: `008_production_readiness` / 37.
- Restored counts: bookings 3, jobs 3, payments 6, vendors 3, workers 3.

## Frontend/build evidence

- Frozen install, lint (4/4 uncached), typecheck (4/4 uncached), and production build: passed.
- Unit/component/API client tests: 35 passed.
- Chromium mock E2E: 26 passed in 33.4 seconds.
- Widths: 375, 430, 768, 1024, 1280, 1440; focus/skip-navigation smoke passed.
- Shared first-load JavaScript: 102 kB; route loads: 106–115 kB.

Firefox, WebKit, manual accessibility, axe, live-provider browser tests, persona UAT,
performance/load baselines, and a production-like deployment rehearsal remain unexecuted.

## Production reinspection

Read-only inspection of `49.12.145.107` at `2026-08-12 12:17 UTC` found:

- Root: 436 GB, 410 GB used, 4.3 GB available, 99%.
- Docker: 587 images / 341.9 GB (71.48 GB reported reclaimable); containers 23.35 GB
  (23.03 GB reported reclaimable); volumes 13.88 GB; build cache 56.11 GB.
- Backups 5.4 GB; `/root/.cache` 6.9 GB; journal 688 MB.
- BREERO PostgreSQL, Redis, and API still publish ports 5432, 6379, and 8000 on IPv4/IPv6.
- Shared Caddy owns 80/443, mounts `/srv/codestra/Caddyfile`, and validates with non-fatal
  formatting/header warnings. No Caddy mutation was made.
- Running source: `8fd87dfc8e5c76fc1990cce7ad84f120af30eb4f`, not an immutable artifact of this branch.
- Database, Redis, and JWT settings are configured. Stripe, geocoding, Odoo, email, SMS, and
  payout are missing or unverified. Secret values were not printed.

The apex resolves externally to `13.248.243.5` and `76.223.105.230`. `api`, `www`, `staging`,
and `staging-api` returned no IPv4 answers.

## Decision

Open P1 defects: #17 disk safety, #18 isolated staging/UAT/DNS/providers, and #19 public ports
plus deployed schema drift. No P0 was observed; P2/P3 classification awaits formal UAT.

**NOT READY FOR STAGING UAT. PRODUCTION NO-GO.** No live service, database, Caddy, DNS, image,
or secret mutation was performed.
