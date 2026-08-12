# Transaction and external-call ownership

Application command boundaries own commits. Repositories and reusable domain helpers mutate,
add, and flush only. Job completion is one database transaction containing the completed job,
history event, compensation snapshot, earning, and outbox event.

Intentional split boundaries:

- Outbox claims commit before delivery so locks are not held over Odoo, email, or SMS calls. Claims
  have expiring leases. Delivery is at-least-once; `IntegrationEvent.id` is the stable consumer
  idempotency key.
- Payout submission commits its stable `payout-batch:{id}` key before the provider call. Provider
  retries must use that key, covering a crash after provider success and before transfer persistence.
- Stripe intent creation uses a persisted request hash and stable idempotency key. Webhook state,
  booking/quote settlement, job history, and outbox effects commit together; a failed settlement is
  recorded in a separate failure transaction for retry visibility.
- Geocoding is a request-time lookup performed before address persistence and does not hold row locks.

Exactly-once external delivery is not claimed. Odoo, email, and SMS adapters receive the outbox event
identifier; integrations that support provider-side idempotency must forward it. Providers without
that facility must deduplicate by the event identifier in their adapter or destination mapping.
