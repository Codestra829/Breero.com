# Rollback runbook

Rollback triggers are failed readiness/migration, sustained elevated 5xx, broken auth,
booking/payment failure, unexpected DB locks, worker crash loop, outbox failure, or a major
frontend outage. The named rollback decision maker owns the call.

1. Stop traffic expansion and preserve logs/correlation IDs.
2. Restore the backed-up Caddyfile or route to the recorded old healthy containers; validate
   the full file and gracefully reload shared Caddy.
3. Roll back `BREERO_FRONTEND_IMAGE` with `infra/production/compose.frontend.yml` independently
   when only frontend is affected. Roll back `BREERO_BACKEND_IMAGE` with
   `infra/production/compose.backend.yml` independently when backend is affected.
4. Do not run Alembic downgrade blindly. Determine whether the old application is compatible
   with the migrated schema.
5. If schema incompatibility or data corruption requires restoration, keep the failed database
   intact, restore the verified pre-cutover archive into a new volume/database, validate its
   revision and row counts, and repoint the old application after explicit data-loss approval.
6. Smoke health, auth and read-only customer/ops paths; monitor through recovery and document
   incident timing and customer impact.

Database restore is a business decision because writes after the backup may be lost. Caddy
and application rollback should be rehearsed on staging before GO.
