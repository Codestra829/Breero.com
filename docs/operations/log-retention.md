# Log retention

BREERO production and staging Compose files use Docker `json-file` rotation at 20 MiB and five
files per container (approximately 100 MiB per service). This applies to API, worker, scheduler,
web, PostgreSQL and Redis logs when the target topology is deployed.

| Source | Rotation | Retention | Owner |
|---|---|---|---|
| Docker/FastAPI/worker/web | 20 MiB, 5 files | size bounded | Operations |
| Caddy | daily or 100 MiB | 14 days | Infrastructure |
| journald | daily | 14 days, max 1 GiB | Infrastructure |
| security/audit events | database policy | financial/legal policy; never log secrets | Security/Finance |

Live Docker daemon, journald and shared Caddy settings were not changed. Before cutover,
Infrastructure must apply and verify host-level limits and confirm at least 14 days of useful
incident history remains queryable.
