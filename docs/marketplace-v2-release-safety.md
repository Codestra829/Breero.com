# Marketplace V2 release-safety verification

Branch: `codex/marketplace-v2-release-safety`

## Verified findings

- Booking creation now rejects active services whose server-owned `is_bookable` flag is false.
- Expired tentative/provider-confirmation holds no longer count against service or provider capacity,
  and the expiry worker transitions all expiring hold states to `EXPIRED`.
- Public-submission delivery state now follows the configured middleware transport rather than the
  legacy direct-Odoo flag. Disabled middleware parks eligible CRM events as
  `PENDING_CONFIGURATION`; it cannot finalize them as delivered.
- An explicit communication grant deactivates the matching active channel/purpose suppression while
  retaining the suppression and consent history.
- `FAILED_TERMINAL` remains visible in the private administrative failure list and remains eligible
  for an audited manual retry.

## Public capability authority

`GET /api/v1/public/capabilities` is the canonical public projection of effective runtime behavior.
Composite capabilities such as online payments and instant booking become true only when every
required underlying flag is enabled. Marketplace features default off, and production validation
continues to reject enabling them for the request-only release.

The public intake reads this contract before enabling submission. When instant booking is false,
date and time are labeled as preferences and explicitly as request-only.

## Assumptions and deferred work

- Request intake is available whenever this API build is serving the public-submission routes.
- No database migration is required because the fixes use existing state and configuration fields.
- This workstream does not add Marketplace V2 aggregates, matching, opportunities, quotes, or
  messaging. Those remain in their dependency-ordered implementation branches.
- Payments, paid leads, automatic booking, automatic confirmation, automatic provider assignment,
  marketing, provider self-service, matching, messaging, and reviews remain disabled by default and
  are rejected when enabled in the current production release configuration.

## Verification evidence

### Disposable PostgreSQL/PostGIS method

Database-dependent verification used a dedicated Docker bridge network with an explicit private
test subnet and a dedicated `postgis/postgis:17-3.5` container. The database used an ephemeral
test-only account and database name, exposed no host port, and was reachable only from a disposable
API test container on that network. A shell exit trap removed both the database container and the
network after each run. Production and staging database hosts, networks, credentials, and containers
were never used by the tests.

The complete Alembic chain was applied to an empty database:

```text
alembic upgrade head
alembic current -> 017_provider_credentials (head)
python scripts/check_schema_drift.py -> No destructive schema drift detected
```

No migration was added by this PR because it makes no schema change.

### Exact quality gates

Backend commands:

```text
python -m compileall -q app tests
ruff check apps/api/app apps/api/tests
alembic upgrade head
alembic current
python scripts/check_schema_drift.py
pytest -q tests/integration
pytest -q tests
```

The isolated integration run passed 21 tests. The final full backend run passed 143 tests with zero
failures or skips.

Frontend, shared-contract, and contract commands:

```text
SCHEDULING_ENABLED=false python apps/api/scripts/generate_openapi.py
pnpm contract:check
pnpm --filter @breero/types typecheck
pnpm --filter @breero/api-client typecheck
pnpm --filter @breero/api-client test
pnpm --filter web typecheck
pnpm --filter web test
pnpm --filter web lint
```

The API client suite passed 17 tests and the web suite passed 33 tests. The request-only OpenAPI
check verified 26 required paths and zero exposed booking/payment mutation routes.

Known non-failing warnings:

- Starlette reports that its current `TestClient` integration with `httpx` is deprecated in favor of
  a future `httpx2` integration.
- Alembic reports that `alembic.ini` does not yet declare `path_separator`; it falls back to its
  legacy `prepend_sys_path` parsing.

## Release-gate confirmation

This PR does not enable or change a deployed value for payments, Stripe, online checkout, paid
leads, automatic booking, automatic confirmation, automatic provider assignment, provider
self-service, marketplace matching, messaging, reviews, marketing email, or marketing SMS. Newly
declared marketplace capability flags default to false and are included in the production
request-only rejection validator.

Marketplace V2 aggregates and schema—including ProjectRequest, matching runs/candidates,
opportunities, lead connections, marketplace quotes, conversations, and reviews—are explicitly
deferred and are not introduced by this PR.
