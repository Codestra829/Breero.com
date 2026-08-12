# Public form persistence and delivery

The canonical endpoints are `POST /api/v1/service-requests`, `POST /api/v1/contact`, and
`POST /api/v1/provider-interest`. Each requires an `Idempotency-Key`, applies validation and a
Redis-backed public-form rate limit, rejects the honeypot field, stores a bounded payload, hashes the
source address, and creates an integration event in the same PostgreSQL transaction.

When Odoo is disabled, submissions remain accepted in BREERO with downstream and outbox status
`PENDING_CONFIGURATION`. This is neither external delivery nor data loss. When enabled, the worker
maps service requests, support inquiries, and provider interest into CRM leads. It searches by the
BREERO submission ID before create/update, making worker retries idempotent. Odoo credentials are
server-only and must never appear in frontend configuration or evidence.

The public confirmation means BREERO accepted the intake; it does not promise provider assignment,
service availability, approval, earnings, or a completed job.

Transactional event routes distinguish service request, contact, and provider interest. Enabled
Odoo workers upsert by immutable `x_breero_request_id`, while `x_breero_form_route` keeps consumer,
support/business, and provider pipelines distinguishable and outside browser routing control.
