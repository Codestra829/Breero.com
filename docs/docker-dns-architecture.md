# Docker and DNS architecture

The current BREERO host is `49.12.145.107`. Production names are `breero.com`, `www`, `app`,
`partners`, `ops`, `api`, and `status`. Staging names are `staging`, `app-staging`,
`partners-staging`, `ops-staging`, and `api-staging`. On 2026-08-12 all twelve configured names
resolved to `49.12.145.207`, which is a **DNS mismatch**, not evidence that `.207` is owned or
approved for BREERO. See `docs/current-host-dns-audit-2026-08-12.md`.

Deployment is split into independent stacks:

- `infra/production/compose.frontend.yml`
- `infra/production/compose.backend.yml`
- `infra/production/compose.status.yml`
- `infra/staging/compose.frontend.yml`
- `infra/staging/compose.backend.yml`

Production frontend services join only `breero_frontend_edge`. Production API joins
`breero_backend_edge` and internal `breero_backend_private`. PostgreSQL, Redis, worker, and
scheduler join only the private network. Staging uses the distinct equivalents prefixed
`breero_staging_`, including volumes `breero_staging_postgres` and `breero_staging_redis`.

Only the existing shared Caddy publishes host ports 80 and 443. No application service declares
host ports. Caddy joins the four external frontend/backend edge networks and never joins either
private network. The reviewed route fragment is `infra/Caddyfile.breero`; it must be appended to
a backup of the live Caddyfile, validated as a complete configuration, and reloaded only under
explicit deployment approval.

The proven public web and backend images are tracked separately as immutable `BREERO_WEB_IMAGE`
and `BREERO_BACKEND_IMAGE` digests. `BREERO_CUSTOMER_IMAGE`, `BREERO_PARTNERS_IMAGE`, and
`BREERO_OPS_IMAGE` are reserved but must not be deployed until those applications have runnable
manifests, Dockerfiles, startup commands, and health tests. Updating one Compose project does not
recreate the other. The same independent versioning applies to staging. Do not use `latest` tags.
