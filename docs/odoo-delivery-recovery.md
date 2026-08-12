# Odoo delivery and recovery

Statuses are PENDING, PROCESSING, DELIVERED, RETRYING, PENDING_CONFIGURATION, FAILED_RETRYABLE, and FAILED_TERMINAL. Claims use database row locking and expiring leases. Retry uses bounded exponential backoff with jitter; permanent authentication/authorization/validation errors fail closed. Safe error codes and summaries are stored without payloads or secrets.

Operators use `GET /internal/v1/integrations/odoo/health`, `GET .../deliveries/{event_id}`, `GET .../failures`, and `POST .../deliveries/{event_id}/retry`. All require operations, finance, or admin authentication and must be excluded from public ingress.

Odoo stores unique event ID, idempotency key, and event-type/aggregate/version constraints. A replay returns the existing acknowledgement. During an outage the accepted BREERO submission remains durable; after recovery, the same event creates at most one Odoo record.
