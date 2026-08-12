# BREERO role portals

Partner, Operations, and Admin/Finance are independent Next.js services. Each uses the public HTTPS API and never joins PostgreSQL or Redis networks.

Build with an immutable SHA tag, selecting `partner`, `ops`, or `admin` through `APP_NAME`. Override the image command because the standalone entry path is app-specific:

```sh
docker build -f deploy/portals/Dockerfile --build-arg APP_NAME=partner --build-arg NEXT_PUBLIC_API_BASE_URL=https://api-staging.breero.com/api/v1 -t breero-partner:$GIT_SHA .
docker run --read-only --tmpfs /tmp --user 10001 --network breero_staging_edge --expose 3000 breero-partner:$GIT_SHA node apps/partner/server.js
```

Use the existing shared Caddy for TLS and routing. Never publish port 3000 directly, attach a portal to the private database network, or include API/database credentials.

The portal UI renders only canonical API data. Sections without an API contract are explicitly unavailable rather than populated with fixtures.
