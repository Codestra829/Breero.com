# Backend production deployment

Production uses dedicated `breero-prod-postgres`, `breero-prod-redis`, `breero-prod-api`, and
`breero-prod-worker` services on `breero_prod_private`; only the API additionally joins the shared
proxy edge network. PostgreSQL, Redis and port 8000 have no host publication.

Required sequence:

1. Verify at least 15% host disk headroom, exact-head green CI, and production-only secrets.
2. Create a checksum-recorded backup and restore it into an isolated verification database.
3. Start immutable `breero-api:<git-sha>` services without a public Caddy route.
4. Migrate to `012_service_area_dimensions`, seed the production launch catalog, and verify zero
   active fixture/Berlin services through the internal API.
5. Run live/ready, OpenAPI, auth and persisted-intake canaries. Certify geocoding and Stripe when
   booking depends on them.
6. Back up Caddy, replace only the `api.breero.com` maintenance handler, validate, and gracefully
   reload.

Rollback is a single Caddy upstream reversal to maintenance or the previous healthy API. Do not
point production at staging and do not roll the database back during immediate application rollback.
