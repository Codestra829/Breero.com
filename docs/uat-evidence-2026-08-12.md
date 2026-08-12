# Release evidence — 2026-08-12

## Source baseline

- Backend master: `9a94a82c5ef815191409bf8e462b9fa8fd5b1bee`.
- Frontend master: `cbc85f8e3f6630d712a7265e030e5eca7cdbf1f1`.
- Full-stack acceptance/tested source: `fc1fdbaa4a8b2ac9ee0babfd363b104cdd7a9bf3`.
- Canonical migration head: `008_production_readiness`.
- OpenAPI: 58 paths / 65 operations.
- Frontend: 28 explicit `page.tsx` routes; production build emitted 31 route entries including
  not-found and generated service-detail paths.

## Executed checks

- Frozen pnpm install: pass; 414 packages reused, none downloaded.
- Lint: pass, 4/4 workspaces.
- Typecheck: pass, 4/4 workspaces.
- Unit/component tests: pass, 7 tasks; 11 test files and 35 tests reported across types, UI,
  API client, and web. Turbo warned that web test outputs are not cached; this is non-fatal.
- Production Next build: pass; 31 route entries, shared first-load JS 102 kB, route first loads
  106–115 kB.
- Staging and production Compose configuration: pass with placeholder immutable digests and
  non-secret example values. No containers/images were created.
- `git diff --check`: pass.

These are build checks, not formal UAT. No isolated environment was available, so canonical
or negative live E2E, persona UAT, browser matrix, manual accessibility, performance/load,
PostgreSQL concurrency, staging migration, and backup/restore were not run.

## Read-only production evidence

- Root filesystem: 436 GB, 408 GB used, 5.8 GB available, 99%.
- Docker: 584 images / ~340 GB; containers ~23 GB; volumes ~13 GB; build cache ~54 GB.
- Current BREERO source: full-stack acceptance commit above.
- API image ID `sha256:b7f3f6396b6671d4885989789363f6659dbf802870504b5e8ff8d20a242b0d56`;
  worker image ID `sha256:e1c0da39f316b23dae370603b74e772f1f2d6b4bc4434a0d23cf939722ef49e6`.
- API live/ready endpoints pass, but database is revision `005_booking_integrations`, PostGIS
  3.5.2, 29 public tables; application head is 008.
- PostgreSQL 5432, Redis 6379, and API 8000 are published on all host interfaces.
- Shared Caddy owns 80/443 at `/srv/codestra/Caddyfile`; full config validates with warnings,
  and no BREERO route was found. No Caddy change was made.
- Apex `breero.com` resolves to 13.248.243.5 and 76.223.105.230; API and www returned no IPv4
  answers during inspection.
- JWT, Stripe, geocoder, Odoo, email, SMS, payout and explicit non-local CORS are missing or
  unverified in the running API. No secret values were read into evidence.

## Decision

Staging: **NOT READY** until dedicated capacity, DNS/TLS, credentials and multi-persona seed
exist. Production: **NO-GO** due issues #17, #18 and #19. No live mutation was performed.
