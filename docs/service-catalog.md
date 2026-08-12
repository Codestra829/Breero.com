# BREERO launch service catalog

The canonical launch catalog is defined in `apps/api/app/seed.py`. Launch seeding is explicit,
environment-gated, idempotent, and defaults every service to `quote_required` and non-bookable.
Operators may set `BREERO_BOOKABLE_SERVICE_SLUGS` only for categories with approved service areas,
availability rules, provider capacity, and payment configuration.

The twelve launch slugs are: `plumbing`, `electrical`, `handyman`, `heating`, `cooling`,
`appliance-repair`, `cleaning`, `locksmith`, `painting`, `carpentry`, `moving-help`, and
`home-maintenance`. No universal price or availability is seeded.

Known `e2e-service-*`, `test-*`, `fixture-*`, and `certification-*` rows are made inactive. The old
Berlin `home-repair-visit` row is also made inactive. Unknown rows are never deleted; launch seeding
makes them inactive so linked certification history remains intact.

Run the seed only after migration and with an explicit launch environment:

```sh
APP_ENV=staging python -m app.seed
APP_ENV=production python -m app.seed
```

Never run test fixture factories as launch seed commands.

Service-area records support polygon boundaries plus reusable country, state, city, postal-code,
center and radius dimensions. Provider coverage remains independently represented by provider home
location/radius and capabilities. No Cypress radius or statewide Texas claim is embedded in generic
domain code; an approved launch-area dataset is required before any service becomes bookable.
