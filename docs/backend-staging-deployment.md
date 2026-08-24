# Backend staging deployment

## Certified candidate

- Application candidate: `e3a1c8fa94875b9a83867a385d2d9fbf91d6d788`
- Architecture base: `337e8e9ef47378643d221fb6c97d4ebdfe69e342`
- Runtime migration: `012_service_area_dimensions` (single head)
- Image: `breero-api:e3a1c8fa94875b9a83867a385d2d9fbf91d6d788`
- Image digest: `sha256:a022d9a22786eada2a2c9c9645ae608817b5667ecbb90f453a35a559c86a51b1`

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

Middleware delivery is an explicit opt-in. A disabled deployment uses only
`docker-compose.backend.yml` and requires no middleware secret files. After private-route, CA,
mTLS and HMAC enrollment has passed, create the dedicated egress network once with an explicitly
non-conflicting subnet:

```sh
docker network create --driver bridge --subnet 10.251.12.0/24 \
  --label com.breero.purpose=private-middleware-egress breero_middleware_egress
```

Set the four `BREERO_STAGING_MIDDLEWARE_*_FILE` variables to root-owned files, change
`MIDDLEWARE_ENABLED=true`, and apply both Compose files in order:

```sh
docker compose -f docker-compose.backend.yml -f docker-compose.middleware.yml config --quiet
docker compose -f docker-compose.backend.yml -f docker-compose.middleware.yml up -d worker
```

Never apply the middleware overlay before its files and external network exist.

## Providers

Stripe, email, SMS, geocoding, Odoo, and payout are explicitly disabled because staging credentials
were not available. There is no fake-provider fallback. Provider-dependent UAT remains blocked until
test/sandbox credentials are installed and the corresponding enable flag is deliberately changed.

## Current external origin evidence

As of 2026-08-12, `api-staging.breero.com` resolves to `49.12.145.107` through Cloudflare and Google
DNS and serves the staging API over valid TLS. `staging.breero.com` resolves to the same host and
serves the isolated `breero-staging-web` container over valid TLS. The staging frontend is built with
`NEXT_PUBLIC_API_MODE=live` and the exact staging API origin; it is not a production-frontend alias.
