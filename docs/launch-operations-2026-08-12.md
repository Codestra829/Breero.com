# Production launch operations record — 2026-08-12 12:38 UTC

> Historical inventory below concerns the superseded `.107` target. The approved origin is now
> `49.12.145.207`; all approved DNS names resolve there, but SSH inventory timed out. See
> `docs/docker-dns-architecture.md`. This correction does not constitute cutover approval.

## Frozen candidate

The candidate is frozen for operational evaluation; only P0/P1 launch fixes may change it.

| Item | Frozen value |
|---|---|
| Backend source | `da57218c73f2050ce1d6ed71f92bbeb737195527` |
| Frontend source | `70b22c9b8d4b978c33fe8190f8b2fff956c56e88` |
| Full-stack acceptance | `4954cc7c15ae566acda2e1ae768fbeaf87b1f3bf` |
| Infrastructure source before this record | `0724e43c6c7f9a7e93a0edf75b94c5a9eecf6944` |
| Alembic head | `008_production_readiness` |
| Backend candidate digest | `breero-api@sha256:b2b1c554cf5e0e1ff835ddbaf639b1f7260a8ca36721f0d6f9ab1204cf726257` |
| Frontend artifact | Not built/published as an immutable production artifact |
| OpenAPI | 58 paths / 65 operations; SHA-256 `799c4f399b01d9df99d446c731f2000a9270c240d2c50ac520e63b174e668712` |
| Production Compose | Repository `docker-compose.production.yml`; not deployed |

## Approval matrix

| Approver | Status | Evidence |
|---|---|---|
| Engineering | APPROVED | Explicit launch-operations input |
| Operations | BLOCKED | No named owner/window; host at emergency disk threshold |
| Finance | BLOCKED | No approval; payment/payout providers unavailable |
| Security | BLOCKED | Public database, Redis, and API ports |
| Infrastructure | BLOCKED | No approval; DNS/edge/disk remediation incomplete |
| Business/Product owner | BLOCKED | No named owner or cutover approval |

## Provider and secret readiness

No credential values were printed. Presence does not establish validity.

| Provider | Configured | Credential tested | Sandbox | Production | Callback | Status |
|---|---:|---:|---:|---:|---:|---|
| Stripe | No | No | No | No | No | BLOCKED |
| Odoo | No | No | No | No | No | BLOCKED |
| Geocoding | No | No | No | No | N/A | BLOCKED |
| Email | No | No | No | No | N/A | BLOCKED |
| SMS | No | No | No | No | N/A | BLOCKED |
| Payout/banking | No | No | No | No | No | BLOCKED |

Database URL, Redis URL, JWT access secret, and JWT refresh secret are PRESENT but UNVERIFIED.
Stripe secret/webhook, Odoo URL/database/user/key, geocoder, SMTP/email, SMS, and payout secrets
are MISSING. Owners and deactivation paths have not been assigned.

## Read-only host and edge evidence

At 12:36 UTC, `/dev/md2` was 436 GB total, 413 GB used, 1.2 GB available, and reported 100%.
Memory was healthy (45 GiB available), with 20 CPUs and load averages 5.03/3.55/3.03.
Docker reported 344.7 GB images, 23.35 GB containers, 13.98 GB volumes, and 57.95 GB build
cache. Backups use 5.6 GB, `/root/.cache` 6.9 GB, and journald 688 MB.

The active BREERO volumes are `breero_postgres_data` and `breero_redis_data`; they are DO NOT
TOUCH. Existing verified backups, current stack, rollback images, shared Caddy state/data, and
unknown volumes are also DO NOT TOUCH. Stopped containers, old images, cache, logs, and backup
retention all REQUIRE REVIEW. No global prune or deletion is approved.

PostgreSQL 5432, Redis 6379, and API 8000 are bound on IPv4/IPv6 and were externally reachable.
Shared Caddy owns 80/443, mounts `/srv/codestra/Caddyfile`, and its complete configuration
validates with non-fatal formatting/redundant-header warnings. It was not modified or reloaded.

DNS answers: `breero.com` resolves to `13.248.243.5` and `76.223.105.230`; `api`, `partners`,
`ops`, and `admin` have no IPv4 answers. No frontend production target is verified.

Prometheus, Grafana, Alertmanager, and Loki are running and healthy, but BREERO-specific alerts,
dashboards, ownership, and thresholds have not been proven.

## Gate, rollback, and cutover decision

Pre-cutover failures: UAT incomplete; open P1 issues #17–#19; disk emergency; provider and secret
readiness blocked; frontend artifact absent; DNS invalid; public data-plane ports; no maintenance
window or named rollback authority; no production-like deployment/rollback rehearsal.

Because the gate failed before maintenance, no final production backup, migration, Caddy change,
cutover, financial smoke, observation window, or rollback was attempted. The prior isolated
backup/restore evidence remains valid only for the audit database, not as a final production backup.

Launch status: **NO-GO**.

Required next action order: approve a targeted disk plan; establish at least the documented 20%
capacity margin; name Operations/Finance/Security/Infrastructure/Business owners; verify production
secrets/providers; publish immutable backend/frontend artifacts; fix DNS; rehearse private topology,
backup/restore, Caddy, smoke, and rollback in staging; close all P1 defects; then schedule a new gate.
