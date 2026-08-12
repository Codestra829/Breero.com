# Backup policy

Production policy target: encrypted PostgreSQL custom-format daily backups with 7 daily, 4 weekly
and 3 monthly copies; an encrypted off-host/off-provider copy; daily checksum and archive listing;
quarterly isolated restore drills. Back up deployment manifests, environment-secret references,
checksummed Caddy configuration, and object-storage configuration/metadata alongside the database.

Operations owns execution, Security owns encryption/access review, and Finance signs off on payment
and payout retention. Backups must never contain plaintext secrets in release evidence. Target RPO is
24 hours until WAL/PITR is implemented; proposed PITR RPO is 15 minutes. Target RTO is 60 minutes,
subject to a measured production-equivalent restore.
