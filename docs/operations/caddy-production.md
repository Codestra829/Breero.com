# Caddy production topology

The shared `codestra-prod-caddy-1` owns 80/443 and mounts `/srv/codestra/Caddyfile` read-only.
`caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` passed on 2026-08-12 with
formatting and redundant forwarded-header warnings. No BREERO route was installed or reloaded.

Desired hosts are `breero.com`, `www.breero.com`, `app.breero.com`, `partners.breero.com`,
`ops.breero.com`, and `api.breero.com`. Frontends proxy to the private web service; API proxies to
the private API service. The route must enforce HTTPS, HSTS after domain validation, CSP and other
security headers, encoded response compression, bounded request bodies, explicit upstream timeouts,
request IDs, access-log rotation, and `/health/ready` behavior.

Rehearsal: copy the complete live Caddyfile into an isolated Caddy container, append the proposed
BREERO routes, validate, and exercise host routing against staging upstreams. Cutover command is
`caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile` only after backup and approval.
Rollback restores the checksummed previous file, validates it, and gracefully reloads. This gate is
BLOCKED pending isolated rehearsal, DNS and Infrastructure approval.
