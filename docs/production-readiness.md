# BREERO production runbook

## Current decision

**NO-GO (verified 2026-08-12 00:23 UTC).** The inspected host has only 5.8 GB free on
436 GB (99% used), and the current BREERO
PostgreSQL, Redis, and API ports are published on all host interfaces. The replacement
topology fixes exposure, but must not be started until an operator approves cleanup,
backup, shared-Caddy networking, secrets, and rollback.

The running source is `fc1fdbaa4a8b2ac9ee0babfd363b104cdd7a9bf3`. Its database reports
`005_booking_integrations`, while application head is `008_production_readiness`; no migration
was attempted. The deployed OpenAPI validates at 58 paths / 65 operations. `api.breero.com`
and `www.breero.com` did not return IPv4 answers; the apex resolves to external addresses not
the inspected host. Shared Caddy configuration validates but contains no BREERO route.

This is earlier evidence. Re-run the read-only host inventory immediately before launch; free
space and running containers are volatile operational state.

## Provider launch state

Credential-free tests use fake geocoding, email, SMS, payout, Stripe-event, and Odoo adapters.
Production must provide unique JWT access/refresh secrets and Stripe secret/webhook credentials.
Geocoding, Odoo, email, SMS, and payout integrations may be explicitly disabled only when the
corresponding capability is intentionally unavailable; missing credentials must never silently
select a fake provider in production. Status APIs expose configured/enabled booleans only.

## Acceptance evidence (2026-08-11, isolated host network)

- Fresh database and prior `005_booking_integrations` database both migrated to
  `008_production_readiness`; destructive column/table drift check passed.
- Custom-format `pg_dump` was listed and restored into an isolated database; restored
  revision was `008_production_readiness` with 33 public tables.
- Production image is 106 MB, runs as non-root `breero`, and has zero fixable HIGH/CRITICAL
  findings in Trivy after runtime OS updates.
- Local single-process baseline against isolated empty PostGIS: `GET /services` mean 1.52 ms,
  p95 1.61 ms; coordinate-backed address validation mean 1.77 ms, p95 1.88 ms (50 requests
  each). This is not a networked staging load test and does not establish production SLOs.

## Pre-deploy checklist

- [ ] Review disk inventory; retain current live system, verified database backup, new
  images, rollback images, and migration working space. Target at least 20% free or a
  documented capacity calculation with 2x the verified database backup plus both image sets.
- [ ] Inventory current commit/image digests, Compose config, volumes, network names, and
  health state. Do not prune blindly.
- [ ] Create a custom-format backup: `pg_dump --format=custom --no-owner --no-acl`.
- [ ] Verify backup SHA-256 and restore it into an isolated PostGIS database; run
  `alembic current`, row-count checks, and an API smoke test against the restored copy.
- [ ] Configure all production secrets. `APP_ENV=production` makes the API fail fast for
  missing/default credentials. Rotate any secret ever stored in source or shell history.
- [ ] Approve private DB/Redis topology and shared Caddy network.
- [ ] Verify `api.breero.com` DNS and TLS issuance prerequisites.
- [ ] Agree maintenance window, monitoring owner, rollback trigger, and rollback image.

## Shared Caddy change (operator-approved only)

First back up the live Caddyfile and identify the external Docker network used by Caddy.
Attach only the replacement API service to that network. Add to the existing config:

```caddyfile
api.breero.com {
    encode zstd gzip
    reverse_proxy breero-api-1:8000 {
        health_uri /health/ready
        health_interval 15s
    }
}
```

Run `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` inside the existing
Caddy container before a graceful reload. Do not launch another proxy or bind 80/443.

## Deployment and rollback

1. Record current state and verify the restore-tested backup.
2. Pull the immutable `BREERO_IMAGE` digest; do not build on the host.
3. Run the one-shot `migrate` profile and verify revision `008_production_readiness`.
4. Start replacement DB/Redis/internal workers, then API; wait for readiness.
5. Connect shared Caddy and apply the validated route.
6. Smoke liveness, readiness, OpenAPI, auth, catalog, booking, payment webhook, job, and payout.
7. Monitor error rate, latency, queue/outbox lag, database locks, disk, and container restarts.
8. Remove old services only after explicit acceptance and a stable observation window.

Rollback routes Caddy back to the inventoried old API and restores old services/images.
Do not downgrade schema by default. If the new schema prevents the old app from running,
restore the verified backup to a new volume/database and repoint the old stack. Recommended
baseline: daily full backups plus WAL/PITR for RPO <= 15 minutes; quarterly restore drills;
RTO target <= 60 minutes, subject to measured database size and restore throughput.

## Disk cleanup review candidates

The inventory shows 584 Docker images (~340 GB; reported reclaimable ~70 GB), build cache
(~54 GB; reported reclaimable ~2.6 GB), `/root/.cache` (~7 GB), backups (~5.4 GB), Docker
volumes (~13 GB), stopped containers (~23 GB reclaimable), and system journal (~664 MB).
An operator must map each candidate
to an owner and retention requirement before removal. Safe review actions include build-cache
age reports, dangling-image ownership, stopped-container inspection, per-volume container
references, backup age/checksum inventory, and journal retention policy. Never run blanket
image/volume/system prune commands on this shared host.
