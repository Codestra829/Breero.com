# BREERO frontend container

This directory deploys only the public `apps/web` Next.js application. It never starts or joins
PostgreSQL, Redis, API, worker, queue, payment-handler, or provider networks.

## Build the immutable image

Run from the repository root at the release commit:

```bash
docker build \
  --file deploy/frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_APP_URL=https://breero.com \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.breero.com/api/v1 \
  --build-arg NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY" \
  --tag "breero-web:$(git rev-parse HEAD)" .
```

`NEXT_PUBLIC_*` values are embedded by Next.js during the build. Build only with the production
public origins. Never pass private provider, database, Redis, JWT, SMTP, or webhook secrets.

## Start

Create the edge network once, then copy `.env.frontend.example` to a host-local `.env.frontend`
with mode `0600`. Do not commit the populated file.

```bash
docker network create breero_frontend
export BREERO_FRONTEND_IMAGE="breero-web:<exact-git-sha>"
export BREERO_FRONTEND_NETWORK="breero_frontend"
docker compose --env-file deploy/frontend/.env.frontend \
  -f deploy/frontend/docker-compose.frontend.yml up -d
docker compose --env-file deploy/frontend/.env.frontend \
  -f deploy/frontend/docker-compose.frontend.yml ps
```

The container exposes port 3000 only to `breero_frontend`; it publishes no host port. Existing
shared Caddy may join this edge network and proxy to `breero-web:3000`. Caddy must not attach this
container to backend-private networks.

## Verify

```bash
docker inspect breero-web --format '{{json .NetworkSettings.Ports}}'
docker inspect breero-web --format '{{json .NetworkSettings.Networks}}'
docker exec breero-web node -e "fetch('http://127.0.0.1:3000/health').then(async r=>{console.log(r.status,await r.text());if(!r.ok)process.exit(1)})"
```

Expected: healthy, only the frontend edge network, and no host bindings.
