# DNS cutover plan

Observed on 2026-08-12: `breero.com` and `www.breero.com` resolve to `13.248.243.5` and
`76.223.105.230`; `app`, `partners`, `ops`, and `api` have no A/AAAA results. No DNS was changed.

| Host | Current | Desired | Initial TTL | Rollback | Owner |
|---|---|---|---:|---|---|
| breero.com | 13.248.243.5, 76.223.105.230 | approved edge/origin target | 300 | restore current values | Infrastructure |
| www | same as apex | CNAME to apex or approved edge | 300 | restore current values | Infrastructure |
| app | absent | approved edge/origin target | 300 | remove record | Infrastructure |
| partners | absent | approved edge/origin target | 300 | remove record | Infrastructure |
| ops | absent | restricted approved edge target | 300 | remove record | Security/Infrastructure |
| api | absent | approved Caddy origin target | 300 | remove record | Infrastructure |

Change order: validate staging routes/certificates, lower TTL, publish non-apex hosts, validate TLS
and origin routing, then change apex/www. Verify with authoritative `dig`, public resolvers, TLS
handshakes and HTTP host probes. Status: **NOT READY_FOR_CUTOVER** until targets and approval exist.
