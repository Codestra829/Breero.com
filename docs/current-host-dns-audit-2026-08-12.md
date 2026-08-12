# Current host and DNS audit — 2026-08-12

Recorded at 2026-08-12T14:25:41Z. This was a read-only audit; DNS, Caddy, firewall, Docker,
volumes, and running services were not changed.

## Authority boundary

The current BREERO host public IP is `49.12.145.107`. `49.12.145.207` is not the current or
approved BREERO origin unless it is separately provisioned and explicitly approved. DNS answers
are recorded as routing facts only and are not evidence of server ownership.

## Independent DNS results

Cloudflare `1.1.1.1` and Google `8.8.8.8` returned the same answers. No queried hostname had an
AAAA answer.

| Hostname | Current resolved IP | Intended IP | Result | TTL |
|---|---|---|---|---:|
| `breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 3600 |
| `www.breero.com` | `49.12.145.207` via CNAME `breero.com` | `49.12.145.107` | MISMATCH | 3600 |
| `app.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `partners.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `ops.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `api.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `status.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `api-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `app-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `partners-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `ops-staging.breero.com` | `49.12.145.207` | `49.12.145.107` | MISMATCH | 600 |
| `staging-api.breero.com` | no A/AAAA answer | not configured; canonical name is `api-staging.breero.com` | MATCH | N/A |

No DNS changes were made.

## Current-host read-only inventory

| Area | Evidence |
|---|---|
| Host | `Ubuntu-jammy-latest-amd64-base.zst`; Ubuntu 22.04.5; kernel 5.15.0-181; x86_64 |
| Compute | 20 CPUs; 62 GiB RAM; approximately 44 GiB available; 31 GiB swap |
| Root filesystem | 436 GiB total; 413 GiB used; approximately 1.1 GiB free; 100% reported usage |
| Inodes | 48% used on root filesystem |
| Docker | Engine 29.1.3; Compose 2.40.3; data root `/var/lib/docker` |
| Public sockets | 22, 80, 443, 5432, 6379, and 8000 listen on all IPv4/IPv6 interfaces |
| Caddy | shared `codestra-prod-caddy-1`, Caddy v2.10.2, owns 80/443; config mounted read-only from `/srv/codestra/Caddyfile` |
| Caddy networks | `codestra-prod_codestra` and `trading-network`; not the repository-defined BREERO edge networks |
| Host firewall | UFW inactive; container-network isolation is insufficient while host ports remain published |

Current BREERO data volumes and unknown volumes were not modified. `docker system df` did not
complete during the bounded inventory and is therefore not claimed as current evidence.

## Decision

**BLOCKED.** The current host is not ready for staging activation. Exact blockers are critical disk
pressure; public PostgreSQL, Redis, and FastAPI ports; DNS mismatch; and unvalidated shared-Caddy
membership in the intended split edge networks. The `.207` SSH timeout is retained separately only
as historical incorrect-target evidence.
