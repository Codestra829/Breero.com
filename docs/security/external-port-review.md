# External port review

Read-only local socket and public-IP checks on 2026-08-12 agree:

| Port | Binding | Public-IP result | Gate |
|---|---|---|---|
| 80/tcp | `0.0.0.0` / Caddy | reachable | expected |
| 443/tcp/udp | `0.0.0.0` / Caddy | reachable | expected |
| 5432/tcp | `0.0.0.0` / BREERO PostgreSQL | reachable | **FAIL** |
| 6379/tcp | `0.0.0.0` / BREERO Redis | reachable | **FAIL** |
| 8000/tcp | `0.0.0.0` / BREERO API | reachable | **FAIL** |
| 22/tcp | `0.0.0.0` / sshd | not externally authorized here | REVIEW |

The checked-in production Compose topology publishes none of 5432, 6379 or 8000 and attaches only
the API/web to the approved Caddy network. Replacing the live topology requires a verified backup,
maintenance window, Caddy route rehearsal and rollback. No live bindings or firewall rules were
changed. Hetzner firewall state and a genuinely independent external scan remain required.
