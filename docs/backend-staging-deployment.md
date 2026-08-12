# Backend staging deployment

## Certified candidate

- Application candidate: `2f6eb4e013ca4aac87620de27ede8a5c4bafe5c3`
- Architecture base: `337e8e9ef47378643d221fb6c97d4ebdfe69e342`
- Migration: `009_final_staging_boundaries` (single head)
- Image: `breero-api:2f6eb4e013ca4aac87620de27ede8a5c4bafe5c3`
- Image digest: `sha256:40faf4c463a86c4ea07006d4d16ee52778ff2c0a7d5df7df42e45d1edfa90698`

## Host topology

The isolated `breero-staging` Compose project runs on `49.12.145.107`:

- `breero-staging-api`: `breero_staging_edge` and `breero_staging_private`
- `breero-staging-postgres`: private only, dedicated volume
- `breero-staging-redis`: private only, dedicated volume
- `breero-staging-worker`: private only
- shared `codestra-prod-caddy-1`: edge only

No staging service publishes `8000`, `5432`, or `6379`. The existing legacy BREERO stack still
publishes those ports and requires a separately approved remediation.

Server-local environment files live in `/etc/breero/staging/`, are root-owned mode `0600`, and are
split into API, PostgreSQL, and Redis files. Values must never be copied into Git or reports.

## Operations

Create the external edge network with an explicitly non-conflicting subnet before first start:

```sh
docker network create --driver bridge --subnet 10.251.10.0/24 breero_staging_edge
```

Export the four required Compose variables described in `deploy/staging/README.md`. Start data
services first, run the one-shot migration, then start API and worker. Always use an immutable image
tag. Verify `/health/live`, `/health/ready`, `/openapi.json`, container port bindings, and network
membership after every update.

## Providers

Stripe, email, SMS, geocoding, Odoo, and payout are explicitly disabled because staging credentials
were not available. There is no fake-provider fallback. Provider-dependent UAT remains blocked until
test/sandbox credentials are installed and the corresponding enable flag is deliberately changed.

