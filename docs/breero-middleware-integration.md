# BREERO → Codestra middleware → Odoo

BREERO never holds an Odoo API key. Its durable outbox sends four typed events to the approved
Codestra middleware command route `POST /api/v1/integrations/breero/events`. Middleware validates
HMAC-V2, tenant, environment, audience, scope, event allowlist and idempotency before it queues an
Odoo delivery. Generic Odoo model or method names are prohibited in this contract.

Allowed events are `breero.service_request.created`, `breero.contact_request.created`,
`breero.provider_interest.created`, and `breero.lead_dispute.created`.

Required protected runtime configuration is documented in the staging and production environment
examples. The HMAC secret and Codestra private CA must be read-only mounted files. Private routing
must reach the middleware's private listener; a public-IP hosts-file override is not sufficient.
Keep `ODOO_ENABLED=false` permanently. Set `MIDDLEWARE_ENABLED=true` first in staging only after
private routing, CA verification and identity enrollment are complete.

Middleware must register identity `breero-staging` or `breero-production`, audience
`codestra-middleware-breero-crm`, tenant `breero`, source IP restrictions and only scope
`breero.crm-events.write`. It must persist an audit receipt and its own outbox transactionally,
deduplicate by event ID and idempotency key, reject changed-payload replay, retry transient Odoo
failures, and expose status/reconciliation without returning unrestricted Odoo access.

Certification requires valid and invalid HMAC, expired timestamp, nonce replay, wrong audience,
wrong tenant, wrong environment, excess scope, non-allowlisted event, all four routing canaries,
same-body replay, changed-body conflict, Odoo outage/recovery, reconciliation, and backup/restore.
Production delivery and public API cutover remain disabled until all evidence passes.
