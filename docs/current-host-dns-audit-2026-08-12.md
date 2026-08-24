# Current-host DNS audit — 2026-08-12

Observed at `2026-08-12T17:37:26Z` through Cloudflare `1.1.1.1` and Google `8.8.8.8`.
Both resolvers returned identical records and no AAAA answers.

| Hostname | Current A | TTL | Intended A for this mission | Result |
|---|---:|---:|---:|---|
| `api-staging.breero.com` | `49.12.145.207` | 600 | `49.12.145.107` | MISMATCH |
| `staging.breero.com` | `49.12.145.207` | 600 | `49.12.145.107` | MISMATCH |
| `api.breero.com` | `49.12.145.207` | 600 | unchanged/out of scope | AUDITED ONLY |
| `breero.com` | `49.12.145.107` | 3600 | `49.12.145.107` | MATCH |

Required authorized change for backend staging:

```text
TYPE=A
NAME=api-staging
VALUE=49.12.145.107
```

No DNS change was made. DNS resolution is not evidence of server ownership; `.107` was verified by
authenticated host access and local inventory. `.207` evidence is retained only as an incorrect-target
investigation.
