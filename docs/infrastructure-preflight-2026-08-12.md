# Infrastructure pre-flight hardening

Recorded 2026-08-12T13:45:00Z. No deployment or live infrastructure mutation was performed.

## Runnable application proof

| Surface | Runnable package | Dockerfile | Startup/health contract | Decision |
|---|---|---|---|---|
| Public web | `apps/web/package.json` | `apps/web/Dockerfile` | standalone Next.js; `/` probe | PROVEN in repository; CI runtime gate added |
| Customer | none | none | none | BLOCKED; no container deployed |
| Partners | README placeholder only | none | none | BLOCKED; no container deployed |
| Operations | README placeholder only | none | none | BLOCKED; no container deployed |
| Admin/finance | README placeholder only | none | none | BLOCKED |

The prior four-container frontend definition incorrectly started one web image four times. It now
contains only the runnable web app. Future `BREERO_CUSTOMER_IMAGE`, `BREERO_PARTNERS_IMAGE`, and
`BREERO_OPS_IMAGE` variables (and staging equivalents) are reserved but intentionally not consumed
until independently runnable artifacts exist.

## Environment isolation

Application services read only `*_APP_ENV_FILE`; PostgreSQL reads only `*_POSTGRES_ENV_FILE`; Redis
reads only `*_REDIS_ENV_FILE`. Compose verification rejects provider/JWT keys in data-service env
files. Examples under `infra/env/` demonstrate boundaries without real secrets.

## Health and read-only runtime

API and web have explicit healthchecks in production and staging. Customer, partners, and ops cannot
receive honest healthchecks because they are not runnable. CI builds web and starts it with a
read-only root and only `/tmp` writable as tmpfs, then probes `/` inside the container. Backend
services already use read-only roots and explicit `/tmp`; scheduler state is under `/tmp`.

## Pinned PostGIS

Backend CI uses exactly
`postgis/postgis:17-3.5@sha256:0a23a2b5e4fbd9b4c6980d20ee80dd6b63dec52669379c75a506db58a4116708`
for migrations, drift checks and pytest. A green post-commit CI result is required evidence.

## DNS from two independent resolvers

Cloudflare `1.1.1.1` and Google `8.8.8.8` were queried again at 2026-08-12T14:25:41Z. No AAAA
answers were returned. The intended current-host IP is `49.12.145.107`; DNS resolution is not
treated as proof of host ownership.

| Hostname | Current A/CNAME answer on both | Intended IP | Result | TTL |
|---|---|---|---|---:|
| `breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 3600 |
| `www.breero.com` | CNAME `breero.com`; A `49.12.145.207` | `49.12.145.107` | MISMATCH | 3600 |
| `app.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `partners.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `ops.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `api.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `status.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `app-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `partners-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `ops-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `api-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |

The contradiction was ordering: `api-staging.breero.com` resolves; `staging-api.breero.com` does
not. DNS does not prove host or application readiness.

## Network and Caddy contract

No application/data/frontend service publishes host ports. Approved Caddy edge networks are only
`breero_frontend_edge`, `breero_backend_edge`, `breero_staging_frontend_edge`, and
`breero_staging_backend_edge`. Private networks are internal and must never attach to Caddy. The
Caddy fragment contains only proven web/API upstreams plus separately managed status; placeholder
customer/partner/ops routes were removed.

The current `.107` host was inspected read-only. Root storage reports 100% used with approximately
1.1 GiB free. Existing BREERO PostgreSQL 5432, Redis 6379, and API 8000 are published on all IPv4
and IPv6 interfaces. Shared Caddy owns 80/443 but is not attached to the repository-defined BREERO
edge networks. No host readiness is claimed and no live Caddy/DNS/network/service was changed.

## Independent deployment and rollback

Frontend operations use only `infra/*/compose.frontend.yml` and `BREERO[_STAGING]_WEB_IMAGE`.
Backend operations use only `infra/*/compose.backend.yml` and backend image variables. Neither
manifest references the other artifact. Static separation is validated; real independent rollback
rehearsal remains blocked until authenticated staging access exists.

## Decision

**BLOCKED**. Remaining conditions: remediate `.107` disk capacity through an approved, itemized
procedure; close public 5432/6379/8000 exposure; reconcile all configured DNS records from `.207`
to the intended `.107` only during an authorized DNS change; validate shared Caddy edge membership;
retain customer/partners/ops names inactive until real apps exist; and complete independent
frontend/backend deploy/rollback rehearsal.
