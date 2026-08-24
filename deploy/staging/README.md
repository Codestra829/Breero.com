# BREERO isolated backend staging

This Compose project contains only the API, worker, PostgreSQL/PostGIS and Redis. It publishes no
host ports. Shared Caddy may join `breero_staging_edge`; it must never join
`breero_staging_private`.

Copy the three example environment files to root-owned `0600` files outside Git, replace every
`CHANGE_ME`, and explicitly enable only providers with valid staging credentials. Run migration as
a one-shot job before starting API and worker. Never substitute fake adapters for missing staging
credentials.
