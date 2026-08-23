# BREERO Marketplace V2 Sync and Integrations

## Source ownership

| System | Authority |
|---|---|
| BREERO PostgreSQL | Marketplace demand, matching, opportunities, connections, quotes, bookings, jobs, trust, entitlements and audit |
| Keycloak at auth.codestra.co | Human and machine identity |
| Codestra middleware | Integration authentication, authorization, routing, receipts and downstream delivery |
| Odoo 19 | CRM projection, activities and communication outcomes; never marketplace state |
| Klyrow / Postal | Email delivery |
| Telnexa / Jasmin | SMS delivery |
| n8n | Approved orchestration only |
| Stripe | Payment settlement authority only after activation |

## Outbound path

~~~mermaid
flowchart TD
  A[BREERO command] --> B[PostgreSQL and outbox]
  B --> C[Leased worker]
  C --> D[Codestra and Kong]
  D --> E[Approved downstream]
~~~

The private Codestra route requires mTLS plus HMAC-V2, exact tenant breero, audience, environment, allowlisted event, replay protection and minimal scope. BREERO never receives an unrestricted Odoo credential.

## Outbox

Statuses are PENDING_CONFIGURATION, PENDING, PROCESSING, RETRYABLE, DELIVERED and FAILED_TERMINAL.

Store event contract, idempotency key, attempts, maximum attempts, available_at, lease_owner, lease_until, last error and delivery timestamp. Claim with FOR UPDATE SKIP LOCKED. Commit the lease before an external call. Retry with bounded exponential backoff and jitter.

## Inbox

integration_inbox stores provider, external_event_id, event_type, request_hash, signature result, status, bounded payload, received_at and processed_at. A unique provider/external_event_id constraint guarantees one business effect. Use it for Codestra callbacks, Klyrow, Telnexa, n8n and Stripe later.

## Odoo projection

Odoo receives only approved, versioned business events. Upsert by immutable BREERO ID. Odoo cannot confirm bookings, assign marketplace providers, settle payments, activate providers, resolve disputes, alter credentials or overwrite lifecycle state. Reconciliation compares source version and receipt; it never silently makes Odoo authoritative.

## n8n

Production n8n must run pinned queue-mode workers and webhook processors with concurrency limits, retention, monitoring and credential isolation. Workflows consume versioned events and call approved command APIs. They may not read or write BREERO tables directly.

## Activation and reconciliation

Every integration has configured, enabled and healthy status. Disabled delivery parks at PENDING_CONFIGURATION. Activation is staged, audited and canary-first. Reconciliation reports missing receipts, duplicates, changed-payload conflicts, lag, retries and terminal failures without exposing secrets.
