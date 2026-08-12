# Production cutover checklist

No maintenance window is authorized. Production cutover was not performed.

- [ ] Start time, incident/communication channel and responsible release owner recorded.
- [ ] All six approval groups APPROVED; P1 issues closed with evidence.
- [ ] Disk below 80%; external 5432/6379/8000 closed; firewall independently scanned.
- [ ] Fresh backup checksum/list/isolated restore verified.
- [ ] Backend and all frontend artifact digests verified.
- [ ] DNS changes and rollback values approved; Caddy backup/config validation complete.
- [ ] Migration 005→008 rehearsed, timed and recovery decision recorded.
- [ ] Private application topology deployed by digest and readiness checks pass.
- [ ] Browser/API/database smoke and signed provider callback checks pass exactly once.
- [ ] Monitoring alerts reach named recipients.
- [ ] GO confirmation recorded by Operations, Finance, Security, Infrastructure and Product.
- [ ] Rollback triggers: readiness failure, migration inconsistency, callback inconsistency,
      elevated 5xx/latency, missing business invariants, or alert failure.
- [ ] Rollback executes recorded prior digests/Caddy config and database recovery strategy.
