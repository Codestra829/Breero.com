# Production deployment procedure

## Change control

Before cutover record maintenance start/duration, technical owner, business owner, rollback
decision maker, and observation owner. Require explicit approval after UAT and provider gates.
Use immutable backend and frontend image digests and record their source commits.

Minimum disk gate is 20% free, or an approved capacity calculation retaining the live stack,
verified backup, both new images, rollback images, migration workspace and log growth. The
current 5.8 GB free on a 436 GB filesystem fails this gate.

## Rehearsal and cutover

First run this exact sequence on staging. For production:

1. Announce maintenance; record `docker ps`, images, volumes, networks, current revision and
   Caddy route.
2. Verify disk gate and a fresh custom-format backup, checksum, archive listing and restore.
3. Verify secrets by configured/missing status without printing values.
4. Pull immutable images and run the Compose `migrate` profile.
5. Verify `alembic current`, `heads`, `check`, PostGIS and critical row counts.
6. Start private PostgreSQL/Redis, API, worker, scheduler and web; wait for health.
7. Back up `/srv/codestra/Caddyfile`, add only approved BREERO routes, connect services to the
   existing shared Caddy network, validate the entire config, then gracefully reload.
8. Smoke live/ready, services, address, availability, login, customer bookings and ops jobs;
   run one live-safe booking/payment only with business approval.
9. Observe 5xx, latency, DB pool/locks, Redis, worker/outbox/webhooks, disk, restarts, CPU and
   memory. Retain old artifacts throughout the observation window (minimum 60 minutes).

Never launch a second edge proxy, publish DB/Redis, deploy `latest`, or delete the rollback
path before acceptance.
