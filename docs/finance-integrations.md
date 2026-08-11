# Finance and integration operations

Vendor compensation is configured per vendor with an effective-dated plan. Supported methods are
fixed minor units, basis-point percentage, and a per-service rate. Job completion refuses to create
an earning when no active plan exists. The exact method, values, gross amount, currency, and hold
period are copied into an immutable compensation snapshot; later plan edits cannot rewrite history.

Earnings progress from pending through available and batched to paid. Holds, cancellation, and
reversal are explicit states. Refunds, disputes, reversals, and manual changes are append-only
adjustment records with idempotency keys and audit entries. A scheduled release promotes earnings
whose hold period expired. Batch selection locks eligible rows with `SKIP LOCKED`; an earning's
single `payout_batch_id` prevents duplicate inclusion.

Payout batches require finance/admin review and approval. Submission persists a stable idempotency
key before calling `PayoutGateway`, and records provider transfer ID, timestamp, and status. No live
banking provider is assumed: without one configured the API returns `integration_not_configured`.

Odoo transport is separate from mapping. Defaults are customer/vendor to `res.partner`, booking to
`sale.order`, job to `project.task` (Field Service), and payment/payout to `account.payment`. Vendor
bill creation and deployment-specific custom fields remain ERP policy and should be configured when
the target Odoo modules are known.

Outbox workers claim rows transactionally, retry with exponential backoff, and move exhausted rows
to `DEAD_LETTER`. Finance/admin users can view failures and manually retry them; retry actions are
audited. `/api/v1/integrations/health` reports only configured/not-configured state and provider
names, never secret values.

Production requires external values for Stripe, SMTP, SMS, Geoapify, Odoo, and the selected payout
provider. SMTP is implemented; SMS and payout deliberately remain provider seams until vendors are
selected. PostGIS service-area lookup remains authoritative after geocoding.
