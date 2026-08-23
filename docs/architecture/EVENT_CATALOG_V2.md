# BREERO Marketplace V2 Event Catalog

## Envelope

Every event contains:

| Field | Requirement |
|---|---|
| event_id | UUID, globally unique |
| event_name | Stable dotted name ending in schema version |
| schema_version | Integer |
| aggregate_type and aggregate_id | Authoritative BREERO aggregate |
| aggregate_version | Monotonic per aggregate |
| occurred_at | UTC timestamp |
| correlation_id | End-to-end request or workflow |
| causation_id | Command or prior event |
| tenant_id and legal_entity_id | Explicit boundary when applicable |
| actor | Principal type and nonsecret identifier |
| payload | Bounded contract-specific object |

The event ID is the external-delivery idempotency key. Changed-payload replay with the same key is a conflict.

## Marketplace events

- project_request.created.v1
- project_request.submitted.v1
- project_request.qualified.v1
- project_request.cancelled.v1
- matching.started.v1
- matching.completed.v1
- opportunity.sent.v1
- opportunity.viewed.v1
- opportunity.accepted.v1
- opportunity.declined.v1
- opportunity.expired.v1
- lead.connected.v1
- conversation.message_sent.v1
- quote.sent.v1
- quote.revised.v1
- quote.accepted.v1
- quote.declined.v1
- booking.created.v1
- booking.confirmed.v1
- booking.cancelled.v1
- job.assigned.v1
- job.en_route.v1
- job.arrived.v1
- job.started.v1
- job.completed.v1
- review.submitted.v1
- credential.expiring.v1
- credential.expired.v1
- credential.revoked.v1
- payment.captured.v1
- payment.refunded.v1

Payment events are contract reservations only until payment capability is independently activated.

## Publication and consumption

- Domain state and outbox record commit atomically.
- Producers never call Odoo, n8n, email, SMS or Stripe during the domain transaction.
- Consumers deduplicate by event_id and verify tenant, environment, audience and allowed event.
- Delivery is at-least-once; exactly-once external delivery is not claimed.
- Ordering is guaranteed only per aggregate through aggregate_version.
- Consumers reject an unexpected version and park it visibly rather than guessing.
- PII-minimized event variants are used for analytics and broad automation.
- Schema files live under schemas/events and are checked for backward compatibility in CI.

## Lifecycle

PENDING_CONFIGURATION is used while an integration is deliberately disabled. Activation moves eligible events to PENDING through an audited command. Workers lease rows, use FOR UPDATE SKIP LOCKED, retry transient failures, and expose FAILED_TERMINAL to Operations. Lease expiry permits safe recovery after a worker crash.
