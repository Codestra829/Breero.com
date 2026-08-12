# Restore rehearsal

The existing audit archive `/root/backups/breero-staging-uat-20260812T122000Z/breero-audit.dump`
was previously listed and restored to isolated `breero_restore_uat`; it restored head
`008_production_readiness` and 37 public tables. This is useful engineering evidence but is not a
current production-equivalent backup because the running BREERO database is at 005 and no final
production backup was taken.

Production restore gate: **FAIL/BLOCKED**. A maintenance preflight must create a custom-format dump,
checksum and list it, restore to isolated PostGIS, record duration, verify Alembic revision, PostGIS,
critical table counts and samples across bookings, jobs, payments, earnings and integration events.
The source database must not be overwritten.
