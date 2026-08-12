# Backend staging rollback

Application rollback is independent of database rollback.

1. Record current container IDs, image digest, env file metadata, Caddy target, and health.
2. Set `BREERO_STAGING_API_IMAGE` to a previously certified, migration-compatible immutable digest.
3. Recreate only `api` and `worker`; do not recreate PostgreSQL or Redis.
4. Verify live/ready, worker ping, migration compatibility, contract, and persisted booking reads.
5. If health fails, restore the candidate image and recreate only `api` and `worker`.

Never downgrade migration 009 automatically. The pre-change Caddy configuration backup is
`/srv/codestra/Caddyfile.backup-20260812T173217Z`. Restoring it requires full validation followed by
a graceful reload. Database recovery uses the custom archive in `/var/backups/breero/staging/` and
must target a new isolated database before any destructive decision.

The application-only rehearsal succeeded from the 62-path final candidate to the compatible
60-path prior image and back. Readiness returned 200 for both images, the database remained at 009,
and the worker rejoined after the final image was restored.

Migration 011/012 application rollback is forward-compatible: added nullable payment and
service-area columns and retained PostgreSQL enum values are ignored by the prior image. Reverse the
proxy/container target first; schema downgrade is not part of an emergency rollback.
