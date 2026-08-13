# BREERO frontend production deployment

## Permanent identity

- Public brand: **BREERO** at **https://breero.com**.
- Legal operator: **Codestra LLC DBA Breero.com**.
- Address: **20633 Longenbaugh Rd, Cypress, TX 77433, United States**.
- Support: **support@breero.com**.
- Corporate website: **https://codestra.co**.

Codestra is the legal/operator identity, not a replacement consumer brand.

## Isolation boundary

The frontend is the standalone Next.js image defined by
`deploy/frontend/Dockerfile` and `deploy/frontend/docker-compose.frontend.yml`.
Its only network is `breero_frontend`, shared with the existing edge proxy. The Compose project
contains no API, database, Redis, worker, queue, Odoo, n8n, or payment-handler service. It publishes
no host port and holds no backend secrets.

```text
Internet -> existing shared Caddy -> breero-web:3000
                                      |
                                      +-> HTTPS https://api.breero.com/api/v1

Backend, PostgreSQL, Redis, workers and payment handlers remain separate.
```

## Immutable image and environment

Tag each image with the exact Git SHA or deploy its registry digest. Never use `latest` as the sole
rollback reference. Build-time public configuration is:

- `NEXT_PUBLIC_APP_URL=https://breero.com`
- `NEXT_PUBLIC_API_BASE_URL=https://api.breero.com/api/v1`
- `NEXT_PUBLIC_API_MODE=live`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` only when payment UI is enabled

The populated `.env.frontend` is host-local and must not contain Stripe secrets, webhook secrets,
database/Redis credentials, JWT secrets, SMTP credentials, Odoo secrets, or private API tokens.
See `deploy/frontend/.env.frontend.example` and `deploy/frontend/README.md` for build/start commands.

## Health, operation, and logs

- Health endpoint: unauthenticated `GET /health`, expected HTTP 200.
- Container: `breero-web`.
- Internal port: `3000`; no host binding.
- Start/update: `docker compose --env-file deploy/frontend/.env.frontend -f deploy/frontend/docker-compose.frontend.yml up -d`.
- Stop: `docker compose --env-file deploy/frontend/.env.frontend -f deploy/frontend/docker-compose.frontend.yml stop web`.
- Logs: `docker compose --env-file deploy/frontend/.env.frontend -f deploy/frontend/docker-compose.frontend.yml logs --tail=200 -f web`.

## Existing Caddy route

Inventory and back up the complete live Caddy configuration before any edit. After the parallel
candidate is healthy, the intended route is:

```caddyfile
breero.com {
    encode zstd gzip
    reverse_proxy breero-web:3000
}

www.breero.com {
    redir https://breero.com{uri} permanent
}
```

Use the actual live container name/network. Validate the complete config with `caddy validate`, then
perform a graceful reload. Do not launch a second reverse proxy or restart unrelated services.

## Safe update and rollback

Before cutover, record the old image digest, container inspection, environment-file path and mode,
network membership, health result, Caddy target, and a timestamped Caddy configuration backup.
Start the candidate under a temporary name, verify `/health` and public/policy routes internally,
then change only the existing proxy target.

Rollback is frontend-only:

1. Restore the recorded old Caddy target/configuration.
2. Validate the complete Caddy configuration and gracefully reload it.
3. Verify the old frontend externally.
4. Stop the candidate after traffic is confirmed on the old image.

No database migration or rollback belongs to this procedure. Never prune Docker or remove volumes as
part of a frontend update.
