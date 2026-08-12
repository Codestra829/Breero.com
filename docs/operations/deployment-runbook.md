# Deployment rehearsal and runbook

Status: **BLOCKED / not rehearsed against the exact candidate**.

1. Confirm approvals, maintenance channel and rollback owner.
2. Require disk below 80% and port/firewall remediation plan.
3. Verify immutable backend/frontend digests and signatures/scans.
4. Create, checksum, list and restore-test a fresh backup.
5. Validate Compose and Caddy configurations offline.
6. Pull artifacts by digest; run migration container and verify head 008.
7. Start private DB/Redis, worker/scheduler, API and web without public internal ports.
8. Attach only API/web to shared Caddy network; validate and reload approved routes.
9. Check readiness, migrations, workers, outbox, logs and browser/API smoke tests.
10. Validate sandbox callbacks and monitoring before declaring deployment healthy.

Every command, timestamp, actor, digest and result must be captured during staging rehearsal.
