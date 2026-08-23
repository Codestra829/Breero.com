# BREERO Marketplace V2 API

## Contract rules

API V2 lives under /api/v2 while /api/v1 remains compatible during migration. OpenAPI is authoritative and must be regenerated and contract-tested in every endpoint PR.

All state-changing commands require:

- authenticated principal when not explicitly public;
- server-side permission and tenant checks;
- Idempotency-Key;
- request hash validation;
- a correlation ID;
- explicit domain command handling;
- an audit entry and versioned outbox event in the same transaction.

Use cursor pagination, RFC 7807-style errors, UTC timestamps with address/provider timezone metadata, minor-unit money, ETags or aggregate versions for conflicting edits, and stable operation IDs.

## Public and customer routes

| Method | Route | Purpose |
|---|---|---|
| POST | /api/v2/project-requests | Create draft |
| GET/PATCH | /api/v2/project-requests/{id} | Read or edit authorized draft |
| POST | /api/v2/project-requests/{id}/answers | Save dynamic answers |
| POST | /api/v2/project-requests/{id}/attachments | Upload authorized attachment |
| POST | /api/v2/project-requests/{id}/submit | Submit once |
| POST | /api/v2/project-requests/{id}/cancel | Controlled cancellation |
| GET | /api/v2/project-requests/{id}/matches | Customer-safe match projection |
| GET | /api/v2/project-requests/{id}/quotes | Quote list |
| GET | /api/v2/quotes/{id} | Quote detail |
| POST | /api/v2/quotes/{id}/accept | Idempotent decision |
| POST | /api/v2/quotes/{id}/decline | Idempotent decision |
| GET | /api/v2/conversations | Authorized conversations |
| GET/POST | /api/v2/conversations/{id}/messages | Participant messages |
| POST | /api/v2/conversations/{id}/attachments | Controlled upload |
| POST | /api/v2/conversations/{id}/read | Read cursor |
| GET | /api/v2/bookings/{id} | Booking projection |
| POST | /api/v2/bookings/{id}/reschedule-request | Request, not silent mutation |
| POST | /api/v2/bookings/{id}/cancel | Controlled cancellation |
| GET | /api/v2/jobs/{id}/timeline | Customer-safe timeline |
| POST | /api/v2/jobs/{id}/reviews | Verified review |

## Public provider discovery

- GET /api/v2/providers
- GET /api/v2/providers/{slug}
- GET /api/v2/providers/{slug}/services
- GET /api/v2/providers/{slug}/availability

Public responses expose approved profile fields only, never internal scores, credential documents or customer data.

## Partner routes

- GET /api/v2/partner/opportunities
- GET /api/v2/partner/opportunities/{id}
- POST /api/v2/partner/opportunities/{id}/accept
- POST /api/v2/partner/opportunities/{id}/decline
- GET /api/v2/partner/leads
- POST /api/v2/partner/project-requests/{id}/quotes
- POST /api/v2/partner/quotes/{id}/send
- POST /api/v2/partner/quotes/{id}/revise
- provider organization, members, workers, services, service areas, availability, credentials and settings endpoints
- controlled job commands for en-route, arrive, start and complete

## Operations and administration

- POST /api/v2/ops/project-requests/{id}/match
- GET /api/v2/ops/matching-runs/{id}
- request, opportunity, quote, scheduling, job, provider, exception and integration queues
- audited manual matching, withdrawal, suspension, credential verification and retry commands
- catalog, geography, runtime capabilities, entitlements and policy configuration under admin permissions

No generic status PATCH is allowed for marketplace aggregates.

## Runtime capabilities

GET /api/v2/capabilities returns server-owned capability booleans. The backend rejects disabled commands even if a client ignores this endpoint. Frontends must hide or relabel disabled paths and must never advertise false capability.

Initial V2-safe values keep instant_booking, automatic_assignment, payments, payouts, paid_leads and marketing false.

## Compatibility

The v1 service-request endpoint adapts to ProjectRequest without creating a second source of truth. Deprecation headers and telemetry are required before retiring any v1 path.
