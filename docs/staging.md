# Isolated staging runbook

Staging is a release gate, not a production-host profile. Use a dedicated host or isolated
runner with its own PostGIS and Redis volumes. Never point its environment at production.

## Required inputs

- Immutable `BREERO_API_IMAGE` and `BREERO_WEB_IMAGE` references (digest preferred).
- A secret-managed env file based on `.env.staging.example`.
- Frontend image built with `NEXT_PUBLIC_API_BASE_URL=https://staging-api.breero.com/api/v1`,
  `NEXT_PUBLIC_APP_URL=https://staging.breero.com`, and a Stripe test publishable key.
- Stripe test webhook, geocoder test key, sandbox email, and explicitly fake/test SMS, Odoo,
  and payout adapters where live sandboxes are unavailable.

## Provision and validate

```sh
export BREERO_STAGING_ENV_FILE=/run/secrets/breero-staging.env
export BREERO_API_IMAGE=registry.example/breero-api@sha256:<digest>
export BREERO_WEB_IMAGE=registry.example/breero-web@sha256:<digest>
scripts/release/verify-compose.sh
docker network create breero_staging_frontend_edge
docker network create breero_staging_backend_edge
docker compose -f infra/staging/compose.backend.yml --profile migration run --rm migrate
docker compose -f infra/staging/compose.backend.yml up -d postgres redis api worker scheduler
docker compose -f infra/staging/compose.frontend.yml up -d
docker compose -f infra/staging/compose.backend.yml exec api alembic current
docker compose -f infra/staging/compose.backend.yml exec api alembic heads
docker compose -f infra/staging/compose.backend.yml exec api alembic check
```

Expected revision is `008_production_readiness`. Confirm PostGIS and schema independently:

```sh
docker compose -f infra/staging/compose.backend.yml exec postgres sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select postgis_version();"'
```

The default UAT ports bind only to loopback (`13000` web, `18000` API). A staging edge may
proxy those ports after DNS/TLS approval. Do not publish database or Redis ports.

## Data and backup gate

`app.seed` provides catalog smoke data only. Formal UAT additionally requires deterministic,
synthetic users for every persona, multiple vendors/workers, qualifications, compensation,
and ownership-boundary fixtures. Until that fixture exists and is reviewed, formal UAT is
blocked. Never substitute production PII.

Set explicit source and restore-test containers, then run
`scripts/release/backup_restore_rehearsal.sh`. Retain the archive, SHA-256, restored revision,
table count, and critical row-count comparison as release evidence.

## Current status (2026-08-12)

Not deployed. The only reachable host is the shared production host at 99% disk usage; using
it for staging would violate isolation and disk-safety requirements. Dedicated staging
capacity, DNS, credentials, and the full UAT seed are external blockers.
