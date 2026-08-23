# BREERO Marketplace V2 Domain Model

## Authority

ProjectRequest is the canonical demand aggregate. Booking is a downstream scheduling outcome and Job is field execution. No API, UI, worker, or integration may treat a public form submission, opportunity, quote, or payment attempt as a confirmed booking.

## Canonical lifecycle

~~~mermaid
flowchart TD
  A[Customer intent] --> B[ProjectRequest]
  B --> C[Qualification]
  C --> D[Fulfillment decision]
  D --> E[Matching]
  E --> F[Opportunity]
  F --> G[LeadConnection]
  G --> H[Conversation and Quote]
  H --> I[Booking]
  I --> J[Job]
  J --> K[Verified Review]
~~~

## Aggregate definitions

| Aggregate | Meaning | Owns |
|---|---|---|
| ProjectRequest | Customer demand | service, answers, attachments, address, budget, timing, source and status history |
| MatchingRun | Reproducible eligibility and ranking decision | algorithm version, configuration snapshot, candidates, gates, scores and reasons |
| Opportunity | Controlled invitation to one provider | disclosure level, delivery, response and expiration |
| LeadConnection | Authorized customer/provider relationship | access grant, attribution and revocation |
| Conversation | Participant-scoped communication | messages, attachments, read state and delivery state |
| Quote | Versioned commercial proposal | immutable sent versions, line items, decisions and expiration |
| Booking | Accepted scheduling outcome | slot, provider, worker, accepted quote and cancellation |
| Job | Field execution | assignment, commands, history, evidence, notes and additional work |
| Review | Completed-job trust signal | dimensions, moderation, response and verified-job badge |

## State machines

ProjectRequest:

DRAFT → SUBMITTED → QUALIFYING → MATCHING → MATCHED → QUOTING → BOOKED

Terminal paths: CANCELLED, EXPIRED and UNSERVICEABLE.

Opportunity:

SENT → VIEWED → ACCEPTED or DECLINED. SENT and VIEWED may become EXPIRED or WITHDRAWN.

Quote:

DRAFT → SENT → ACCEPTED or DECLINED. SENT may be REVISED, EXPIRED or WITHDRAWN. A revision creates a new immutable version.

Booking:

PENDING_CONFIRMATION → CONFIRMED → CANCELLED or EXPIRED. The current request-only release must not create or confirm bookings.

Job:

CREATED → ASSIGNED → EN_ROUTE → ARRIVED → DIAGNOSING → AWAITING_APPROVAL → IN_PROGRESS → COMPLETED. Controlled cancellation is permitted from defined nonterminal states.

## Invariants

- Every state change uses a domain command and appends immutable history.
- Aggregate version increases with each accepted command.
- State, history, audit entry and outbox event commit in one database transaction.
- Customer contact data is not disclosed before an authorized LeadConnection.
- A sent quote is immutable; revisions create new versions.
- Quote acceptance is idempotent and does not confirm a booking while runtime capability policy forbids it.
- A verified review requires one completed BREERO job and one eligible customer.
- Marketplace acquisition attribution is preserved as BREERO_MARKETPLACE, PROVIDER_DIRECT, REFERRAL or OTHER.
- Existing v1 bookings and jobs remain historical records and are bridged additively; they are not rewritten.

## Legacy mapping

| Current concept | V2 treatment |
|---|---|
| Public service request | Adapter into ProjectRequest |
| Professional lead | Opportunity plus optional later paid LeadConnection |
| Booking-first intake | Deprecated for new marketplace demand |
| Existing booking and job | Retained and linked with nullable V2 foreign keys |
| Odoo CRM lead | Projection only; never marketplace truth |
