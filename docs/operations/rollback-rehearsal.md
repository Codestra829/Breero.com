# Rollback rehearsal

Status: **FAIL/BLOCKED**. No exact-candidate application/frontend/Caddy rollback was executed.

Rehearsal must deploy the candidate by digest, verify it, deliberately route back to recorded prior
digests, restore the previous Caddyfile, and prove health. Configuration rollback restores the
checksummed prior environment references. Migration 008 must be classified before cutover: if old
code remains compatible, roll back applications without database downgrade; otherwise stop writes,
restore the verified pre-migration backup into a new database, validate it, and repoint only after
explicit data-loss/RPO approval. Forward-fix is preferred for non-destructive additive migrations.
