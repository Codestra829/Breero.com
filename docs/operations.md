# BREERO operations baseline

Monitor API 5xx and latency, readiness, PostgreSQL connections/locks, Redis health, worker and
scheduler restarts, task failures, outbox lag, Stripe webhook failures, disk/inodes, memory and
CPU. Alerts require an owner and tested notification path.

Post-deploy smoke endpoints are `/health/live`, `/health/ready`, `/api/v1/services`, address
validation, availability, login, customer bookings and ops jobs. Mutating booking/payment
smoke requires approved safe test identities and payment method.

Backups should be encrypted, access-controlled and stored off-host. Record timestamp, size,
SHA-256, Alembic revision and restore-test result. Do not count an archive as a backup until
`pg_restore --list` and an isolated restore succeed.

On the shared host, inventory before cleanup. Safe-to-remove candidates require proof of no
references and retention approval. Old images, backups and application logs require owner
review. Active/unknown volumes, current backups, Caddy configuration and active data are never
cleanup targets. Never use a global Docker prune.

Provider health must distinguish live, sandbox/fake and unconfigured. Fake SMS/Odoo/payout
adapters are acceptable only as documented staging limitations, never represented as live.
