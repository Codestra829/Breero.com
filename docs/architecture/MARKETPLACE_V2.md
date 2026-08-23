# BREERO Marketplace V2 — Unified Architecture Authority

Status: planning authority; documentation only.

Base: codex/breero-production-without-payments at c48e5deb2880657396ce5a9eac51a35ff7ecfdde

The current release remains request-only and manual-dispatch-first. Payments, paid leads, payouts, automatic assignment, automatic confirmation, and marketing stay disabled until their later phases are independently implemented, tested, approved, and activated.

Roadmap authority: the detailed branch list and merge order in section 37 supersede any abbreviated numbering in section 1. The executable sequence is PR-00 through PR-17.

The existing PR-0 work already covers `is_bookable`, expired holds, middleware parking, consent re-opt-in, `FAILED_TERMINAL`, runtime capabilities, TypeScript contracts, public intake behavior, and tests, but according to the execution log it still needed final database-backed validation and publication. 

## Complete Git implementation plan

## Target repository

```
```
appolon1908-hue/Breero.com
```

Current implementation base:

```
```
codex/breero-production-without-payments
```

Do not build the new marketplace from the older `main` snapshot until the production candidate is reconciled.

---

# 1. Git strategy

Use small sequential PRs.

Do not create one permanent giant feature branch.

The flow should be:

```
```
codex/breero-production-without-payments
        │
        ├── PR-00 release safety
        │
        ├── PLAN architecture authority
        │
        └── after PR-00 merges
                 │
                 ├── PR-01 ProjectRequest
                 ├── PR-02 Provider platform
                 ├── PR-03 Matching
                 ├── PR-04 Opportunities
                 ├── PR-05 Quotes
                 ├── PR-06 Messaging
                 ├── PR-07 Customer marketplace
                 ├── PR-08 Provider SaaS
                 ├── PR-09 Operations
                 ├── PR-10 Reviews / trust
                 ├── PR-11 Analytics
                 ├── PR-12 Integration reliability
                 ├── PR-13 Payments
                 └── PR-14 Azure modernization
```

After each PR merges, the next branch should be created from the latest merged target.

Do not maintain a 14-level branch chain if avoidable.

---

# 2. Architecture planning branch

Branch:

```
```
planning/breero-marketplace-v2-unified-architecture
```

Base:

```
```
codex/breero-production-without-payments
```

This branch is documentation only.

Add:

```
```
docs/architecture/
├── MARKETPLACE_V2.md
├── DOMAIN_MODEL_V2.md
├── DATA_MODEL_V2.md
├── API_V2.md
├── EVENT_CATALOG_V2.md
├── MATCHING_ENGINE_V2.md
├── SYNC_INTEGRATIONS_V2.md
├── SECURITY_RBAC_V2.md
├── UX_DESIGN_V2.md
├── PROVIDER_SAAS_V2.md
├── OPS_COMMAND_CENTER_V2.md
├── MIGRATION_PLAN_V2.md
├── OBSERVABILITY_V2.md
└── AZURE_TARGET_V2.md

docs/codex/
├── MARKETPLACE_V2_MASTER_MISSION.md
├── MARKETPLACE_V2_IMPLEMENTATION_RULES.md
└── MARKETPLACE_V2_ACCEPTANCE_TESTS.md
```

Update:

```
```
docs/codex/MASTER.md
docs/architecture/system.md
README.md
```

Commit:

```
```
docs: define unified marketplace v2 architecture
```

Draft PR:

```
```
[PLAN] BREERO Marketplace V2 — unified UX, API, data and sync architecture
```

---

# 3. Canonical architecture

The planning branch must establish this lifecycle as authoritative:

```
```
Customer Intent
      ↓
ProjectRequest
      ↓
Qualification
      ↓
Fulfillment Decision
      ↓
Matching
      ↓
Opportunity
      ↓
LeadConnection
      ↓
Conversation + Quote
      ↓
Booking / Scheduling
      ↓
Job
      ↓
Verified Review
```

Definitions:

```
```
ProjectRequest
= customer demand

Matching
= provider eligibility + ranking

Opportunity
= controlled invitation to a provider

LeadConnection
= authorized marketplace connection

Quote
= commercial proposal

Booking
= accepted scheduling outcome

Job
= field execution

Review
= completed-job trust signal
```

This distinction should drive the API, database, portals, events, and reporting.

---

# 4. PR-00 — Release safety

Branch:

```
```
codex/marketplace-v2-release-safety
```

This branch already has substantial implementation work.

Finish:

```
```
Service.is_bookable enforcement
Expired hold capacity behavior
Hold expiration worker
Middleware disabled → PENDING_CONFIGURATION
Middleware enable → safe activation
Consent re-opt-in
FAILED_TERMINAL visibility
Runtime capability endpoint
Frontend capability consumption
Request-only messaging
OpenAPI regeneration
Regression tests
```

Also require:

```
```
PostgreSQL/PostGIS integration tests
Alembic migration validation
Outbox activation lifecycle test
Outbox retry/idempotency test
Email/SMS consent isolation tests
```

Draft PR:

```
```
[V2-00] Harden request-only release and add runtime capability authority
```

Do not introduce Marketplace V2 schema here.

---

# 5. PR-01 — ProjectRequest core

Branch:

```
```
codex/marketplace-v2-project-requests
```

This is the first new marketplace domain.

## Database

Add:

```
```
project_requests
project_request_answers
project_request_attachments
project_request_status_history
```

Recommended `project_requests`:

```
```
id UUID PK
reference VARCHAR UNIQUE

customer_id UUID NULL
service_id UUID NOT NULL
address_id UUID NOT NULL
legal_entity_id UUID NULL

status
fulfillment_mode

description TEXT
urgency

budget_min_minor BIGINT NULL
budget_max_minor BIGINT NULL
currency CHAR(3)

preferred_start_at TIMESTAMPTZ NULL
preferred_end_at TIMESTAMPTZ NULL

source
submitted_at
expires_at

version INTEGER

created_at
updated_at
```

Statuses:

```
```
DRAFT
SUBMITTED
QUALIFYING
MATCHING
MATCHED
QUOTING
BOOKED
CANCELLED
EXPIRED
UNSERVICEABLE
```

Fulfillment:

```
```
INSTANT_BOOK
QUOTE_REQUIRED
MANUAL_DISPATCH
UNSERVICEABLE
```

## Domain

Add:

```
```
apps/api/app/domains/project_requests/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── commands.py
├── events.py
└── policies.py
```

## API

```
```
POST   /api/v2/project-requests
GET    /api/v2/project-requests/{id}
PATCH  /api/v2/project-requests/{id}

POST   /api/v2/project-requests/{id}/answers
POST   /api/v2/project-requests/{id}/attachments

POST   /api/v2/project-requests/{id}/submit
POST   /api/v2/project-requests/{id}/cancel
```

## Events

```
```
project_request.created.v1
project_request.submitted.v1
project_request.cancelled.v1
project_request.qualified.v1
```

## Done when

```
```
customer can create draft
save answers
attach files
submit
cancel
retrieve request
state history persists
duplicate submission is safe
authorization is enforced
```

---

# 6. PR-02 — Provider marketplace foundation

Branch:

```
```
codex/marketplace-v2-provider-profiles
```

Add/extend:

```
```
provider_organizations
provider_profiles
provider_workers
provider_services
provider_service_areas

provider_availability_rules
provider_availability_exceptions

credential_requirements
provider_credentials
credential_verifications
provider_documents
```

## Provider profile

Support:

```
```
display name
slug
description
years in business
service list
gallery
service areas
rating projection
verified jobs
response-time metric
trust badges
```

Public:

```
```
GET /api/v2/providers
GET /api/v2/providers/{slug}
GET /api/v2/providers/{slug}/services
GET /api/v2/providers/{slug}/availability
```

Public page:

```
```
/pros/{slug}
```

---

# 7. PR-03 — Availability and credentials

This may be kept with PR-02 if small, but if the diff gets large, split it.

Branch:

```
```
codex/marketplace-v2-provider-trust-availability
```

Availability:

```
```
provider_availability_rules
provider_availability_exceptions
```

Support:

```
```
timezone
weekday
start/end
capacity
worker-specific schedule
effective dates
blackouts
exceptions
variable capacity
```

Credentials:

```
```
PENDING
VERIFIED
REJECTED
EXPIRED
REVOKED
```

Credential requirements depend on:

```
```
service
jurisdiction
subject type
provider/worker
```

Expired required credential must make provider ineligible.

---

# 8. PR-04 — Matching engine

Branch:

```
```
codex/marketplace-v2-matching
```

Database:

```
```
matching_runs
match_candidates
match_reasons
```

Hard gates:

```
```
provider active
service supported
service area valid
credentials valid
insurance valid where required
not suspended
worker qualified
availability
capacity
legal entity constraints
```

Ranking:

| SignalWeight                   |    |
| ------------------------------ | -- |
| Availability                   | 20 |
| Distance/service area          | 20 |
| Verified rating                | 15 |
| Completion rate                | 10 |
| Opportunity acceptance         | 10 |
| Response speed                 | 10 |
| Price competitiveness          | 5  |
| Existing customer relationship | 5  |
| Breero quality score           | 5  |

Store:

```
```
algorithm_version
configuration_snapshot
eligibility
rejection reasons
score components
rank
final score
```

API:

```
```
POST /api/v2/ops/project-requests/{id}/match
GET  /api/v2/ops/matching-runs/{id}
GET  /api/v2/project-requests/{id}/matches
```

Events:

```
```
matching.started.v1
matching.completed.v1
```

---

# 9. PR-05 — Opportunities and LeadConnection

Branch:

```
```
codex/marketplace-v2-opportunities
```

Database:

```
```
opportunities
lead_connections
```

Opportunity states:

```
```
SENT
VIEWED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN
```

Rules:

```
```
do not reveal full customer PII to every match
send approximately top 3 providers initially
record offer history
do not overwrite prior assignment/offer history
```

Partner API:

```
```
GET  /api/v2/partner/opportunities
GET  /api/v2/partner/opportunities/{id}

POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

GET /api/v2/partner/leads
```

Events:

```
```
opportunity.sent.v1
opportunity.viewed.v1
opportunity.accepted.v1
opportunity.declined.v1
opportunity.expired.v1

lead.connected.v1
```

---

# 10. PR-06 — Quotes

Branch:

```
```
codex/marketplace-v2-quotes
```

Database:

```
```
quotes
quote_versions
quote_line_items
```

States:

```
```
DRAFT
SENT
REVISED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN
```

Rules:

```
```
sent quotes immutable
revision creates new version
customer acceptance idempotent
accepted quote does not imply confirmed appointment unless runtime policy permits
```

Partner:

```
```
POST /api/v2/partner/project-requests/{id}/quotes
POST /api/v2/partner/quotes/{id}/send
POST /api/v2/partner/quotes/{id}/revise
```

Customer:

```
```
GET  /api/v2/project-requests/{id}/quotes
GET  /api/v2/quotes/{id}
POST /api/v2/quotes/{id}/accept
POST /api/v2/quotes/{id}/decline
```

Events:

```
```
quote.sent.v1
quote.revised.v1
quote.accepted.v1
quote.declined.v1
```

---

# 11. PR-07 — Messaging

Branch:

```
```
codex/marketplace-v2-messaging
```

Database:

```
```
conversations
conversation_participants
messages
message_attachments
message_delivery_status
```

Message types:

```
```
TEXT
IMAGE
DOCUMENT
QUOTE
APPOINTMENT_PROPOSAL
SYSTEM
```

API:

```
```
GET  /api/v2/conversations
GET  /api/v2/conversations/{id}

GET  /api/v2/conversations/{id}/messages
POST /api/v2/conversations/{id}/messages

POST /api/v2/conversations/{id}/attachments
POST /api/v2/conversations/{id}/read
```

Security:

```
```
participant membership required
provider tenant boundary
attachment authorization
signed/controlled download
content size/type validation
```

Critical negative test:

```
```
Provider A cannot read Provider B conversation
```

---

# 12. PR-08 — Booking and Job bridge

Branch:

```
```
codex/marketplace-v2-booking-job-bridge
```

Connect V2 to the existing fulfillment system.

Booking should gain:

```
```
project_request_id
accepted_quote_id
provider_id
worker_id
```

Do not rewrite historical bookings.

Job states:

```
```
CREATED
ASSIGNED
EN_ROUTE
ARRIVED
DIAGNOSING
AWAITING_APPROVAL
IN_PROGRESS
COMPLETED
CANCELLED
```

Maintain:

```
```
job_status_history
job_assignments
job_notes
job_evidence
job_additional_work
```

API:

```
```
GET  /api/v2/bookings/{id}
POST /api/v2/bookings/{id}/reschedule-request
POST /api/v2/bookings/{id}/cancel

GET  /api/v2/jobs/{id}
GET  /api/v2/jobs/{id}/timeline

POST /api/v2/jobs/{id}/en-route
POST /api/v2/jobs/{id}/arrive
POST /api/v2/jobs/{id}/start
POST /api/v2/jobs/{id}/complete
```

---

# 13. PR-09 — Customer marketplace UI

Branch:

```
```
codex/marketplace-v2-customer-experience
```

Redesign `apps/web`.

## Homepage

Primary hero:

```
```
What do you need help with?

[ My kitchen sink is leaking... ]

[ ZIP code ] [ Find qualified professionals ]
```

Categories below.

## Request wizard

```
```
1 Service/need
2 Dynamic questions
3 Description
4 Photos/files
5 Address/property
6 Urgency/timing
7 Review
8 Submit
```

## Customer account

```
```
Requests
Matches
Quotes
Messages
Bookings
Jobs
Reviews
Properties
Profile
```

## Provider comparison

Show:

```
```
provider
rating
verified jobs
trust
distance
response time
quote
availability
```

---

# 14. PR-10 — Provider SaaS

Branch:

```
```
codex/marketplace-v2-provider-saas
```

Redesign `apps/partner`.

Navigation:

```
```
Overview
Opportunities
Leads
Quotes
Messages
Schedule
Jobs
Customers
Workers
Services
Service Areas
Availability
Credentials
Reviews
Analytics
Billing
Settings
```

Dashboard:

```
```
new opportunities
open quotes
jobs today
response rate
completion rate
credential warnings
revenue when enabled
```

Eventually provider-created CRM customers may exist outside Breero marketplace acquisition.

Keep attribution:

```
```
BREERO_MARKETPLACE
PROVIDER_DIRECT
REFERRAL
OTHER
```

---

# 15. PR-11 — Operations command center

Branch:

```
```
codex/marketplace-v2-ops-command-center
```

Redesign `apps/ops`.

Main areas:

```
```
Requests
Matching
Jobs
Providers
Exceptions
Map
```

Queues:

```
```
unmatched
awaiting provider
awaiting quote
scheduling
unassigned
late
at risk
credential issue
stale opportunity
integration failure
```

Matching inspector shows:

```
```
candidate
eligible?
reason
distance
credentials
availability
capacity
score breakdown
rank
```

Manual actions must produce audit events.

---

# 16. PR-12 — Reviews and trust

Branch:

```
```
codex/marketplace-v2-reviews-trust
```

Database:

```
```
reviews
review_dimensions
review_responses
review_moderation
```

Only:

```
```
COMPLETED BREERO JOB
```

may create a verified marketplace review.

Dimensions:

```
```
overall
quality
communication
timeliness
value
```

Public badge:

```
```
Verified Breero Job
```

Do not let unverified reviews influence matching score.

---

# 17. PR-13 — Analytics

Branch:

```
```
codex/marketplace-v2-analytics
```

Track:

```
```
visitor
request_started
request_submitted
qualified
matched
opportunity_sent
opportunity_accepted
quote_sent
quote_accepted
booking_created
job_completed
review_submitted
repeat_request
```

Metrics:

```
```
request conversion
serviceability
match rate
time to match
provider response time
opportunity acceptance
quote rate
quote-to-book
completion
cancellation
dispute
repeat customer
provider retention
AOV when enabled
GMV when enabled
take rate when enabled
```

---

# 18. PR-14 — Integration reliability

Branch:

```
```
codex/marketplace-v2-integration-reliability
```

This is important before serious production automation.

## Outbox

Canonical statuses:

```
```
PENDING_CONFIGURATION
PENDING
PROCESSING
RETRYABLE
DELIVERED
FAILED_TERMINAL
```

Recommended fields:

```
```
id
event_type
aggregate_type
aggregate_id
schema_version
payload

status
idempotency_key

attempt_count
max_attempts
available_at

lease_owner
lease_until

last_error_code
last_error_at

created_at
delivered_at
```

Claim with:

```
```
FOR UPDATE SKIP LOCKED
```

## Inbox

Add:

```
```
integration_inbox
```

Fields:

```
```
provider
external_event_id
event_type
request_hash
signature_verified
status
payload
received_at
processed_at
```

Unique:

```
```
(provider, external_event_id)
```

Use for:

```
```
Codestra callbacks
Klyrow
Telnexa
Stripe later
other webhook providers
```

---

# 19. Event catalog

Create versioned contracts.

```
```
project_request.created.v1
project_request.submitted.v1
project_request.qualified.v1

matching.started.v1
matching.completed.v1

opportunity.sent.v1
opportunity.viewed.v1
opportunity.accepted.v1
opportunity.declined.v1
opportunity.expired.v1

lead.connected.v1

quote.sent.v1
quote.revised.v1
quote.accepted.v1
quote.declined.v1

conversation.message_sent.v1

booking.created.v1
booking.confirmed.v1
booking.cancelled.v1

job.assigned.v1
job.en_route.v1
job.arrived.v1
job.started.v1
job.completed.v1

review.submitted.v1

credential.expiring.v1
credential.expired.v1
credential.revoked.v1

payment.captured.v1
payment.refunded.v1
```

Every event should define:

```
```
event ID
event name
schema version
aggregate ID
aggregate version
occurred_at
correlation ID
causation ID
tenant/legal entity
payload
```

---

# 20. Codestra integration

Breero should remain source of truth.

```
```
BREERO
Marketplace system of record

CODESTRA
integration/control plane

ODOO
CRM projection

KLYROW
email provider

TELNEXA
SMS provider

STRIPE
payment authority only after activation
```

Recommended path:

```
```
Breero transaction
       ↓
Breero DB + Outbox
       ↓
Worker
       ↓
Codestra/Kong
       ↓
┌──────────┬──────────┬──────────┐
Klyrow    Telnexa      Odoo    approved automation
```

Preserve the production controls from the Codestra mission: explicit auth, tenant isolation, gateway boundaries, idempotency, replay protection, controlled activation, and no unapproved external side effects. 

---

# 21. API V2 organization

Add:

```
```
apps/api/app/api/v2/
├── router.py
├── public.py
├── catalog.py
├── project_requests.py
├── providers.py
├── customer.py
├── partner.py
├── opportunities.py
├── quotes.py
├── conversations.py
├── bookings.py
├── jobs.py
├── reviews.py
├── operations.py
├── admin.py
└── integrations.py
```

Keep `/api/v1` working during migration.

Do not destructively rewrite V1.

---

# 22. Runtime capability registry

Expand the existing capability authority.

Eventually:

```
```
{
  "request_intake": true,
  "marketplace_matching": true,
  "provider_opportunities": true,
  "provider_self_service": true,
  "quotes": true,
  "messaging": true,
  "reviews": true,

  "instant_booking": false,
  "automatic_assignment": false,

  "payments": false,
  "payouts": false,
  "paid_leads": false,

  "marketing": false
}
```

The UI must not claim capabilities that are false.

---

# 23. RBAC

Roles:

```
```
CUSTOMER

PROVIDER_OWNER
PROVIDER_MANAGER
WORKER

DISPATCHER
CUSTOMER_SUPPORT
TRUST_SAFETY
FINANCE

ADMIN
SUPER_ADMIN
```

Permissions:

```
```
project_request.read
project_request.manage

matching.run

opportunity.read
opportunity.respond

quote.create
quote.send
quote.accept

conversation.read
conversation.send

job.assign
job.execute
job.complete

credential.verify
provider.suspend

finance.refund
finance.payout.approve

admin.feature.manage
```

Server-side authorization is mandatory.

Do not rely on hidden buttons.

---

# 24. Shared UI package

Add to `packages/ui`:

```
```
ProviderCard
ProviderRating
VerifiedBadge
CredentialBadge

ProjectRequestCard
RequestStatus

OpportunityCard

MatchScore
MatchReason

QuoteCard
QuoteBuilder
QuoteComparison

Conversation
MessageBubble
MessageComposer

JobCard
JobTimeline

AvailabilityPicker

ReviewCard

ServiceAreaMap
```

---

# 25. Search and geography

PostGIS remains authoritative.

Provider areas should use geographic geometry/geography.

Use:

```
```
GiST index
ST_Covers
ST_DWithin
distance sorting
```

Later:

```
```
PostgreSQL
    ↓
projection
    ↓
Azure AI Search / OpenSearch
```

Search is not source of truth.

---

# 26. Redis rules

Redis may store:

```
```
rate limits
cache
availability projections
candidate cache
short-lived locks
Celery state/queues
```

Redis must not be authoritative for:

```
```
ProjectRequest
Quote
Job
Review
Credential
Payment
```

---

# 27. PR-15 — Payments

Branch:

```
```
codex/marketplace-v2-transactions
```

Do not begin until the quote → booking → job lifecycle is stable.

Add:

```
```
payment_intents
payments
payment_allocations
refunds
platform_fees
provider_balances
payouts
```

Rules:

```
```
Stripe webhook authoritative
browser redirect not authoritative
idempotent webhook handling
idempotent capture
explicit fee
explicit refund
payout separate from customer payment
finance authorization
full audit
```

Support future monetization:

```
```
transaction fee
subscription
paid lead
hybrid
```

Do not hard-code the entire marketplace to one revenue model.

---

# 28. PR-16 — Provider subscriptions

Branch:

```
```
codex/marketplace-v2-provider-subscriptions
```

Possible future plans:

```
```
FREE
PRO
BUSINESS
```

Capabilities may include:

```
```
CRM
quotes
scheduling
analytics
priority profile
lead limits
team seats
automation
```

Keep feature entitlement separate from RBAC.

---

# 29. PR-17 — Azure modernization

Branch:

```
```
codex/marketplace-v2-azure-modernization
```

Do this after application stabilization.

Target:

```
```
Azure Front Door
       ↓
WAF/CDN
       ↓
Next.js apps
       ↓
API Management
       ↓
Azure Container Apps
 ├── FastAPI
 └── workers
       ↓
PostgreSQL Flexible Server + PostGIS
Managed Redis
Service Bus
Blob Storage
Key Vault
Application Insights
Azure Monitor
Defender
```

Do not introduce AKS unless there is a documented requirement.

---

# 30. Database migration policy

Every schema PR gets an Alembic migration.

Rules:

```
```
additive first
no destructive history rewrite
no production DB testing
migration upgrade tested
downgrade where practical
explicit backfill scripts
validate backfills before constraints
no hidden data conversion
```

Do not assume migration numbers.

Use the actual current Alembic head.

---

# 31. Required testing for every PR

Backend:

```
```
unit tests
domain transition tests
repository tests
PostgreSQL integration tests
authorization tests
negative authorization tests
migration tests
idempotency tests
concurrency tests where applicable
```

Frontend:

```
```
typecheck
lint
component tests
API contract tests
responsive tests
accessibility tests
```

Integration:

```
```
outbox behavior
inbox idempotency
duplicate delivery
retry
lease expiry
external failure
feature disabled
```

---

# 32. Critical security acceptance tests

These should exist before production marketplace activation:

```
```
Provider A cannot access Provider B opportunity

Provider A cannot access Provider B quote

Provider A cannot access Provider B conversation

Provider A cannot access Provider B customer PII

Provider A cannot access Provider B job

Customer cannot access another customer's request

Worker cannot execute another provider's job

Dispatcher cannot approve payout

Support cannot verify credential

Expired credential cannot match

Suspended provider cannot match

Unmatched provider cannot receive customer contact data
```

---

# 33. Critical reliability acceptance tests

```
```
duplicate ProjectRequest submit
→ no duplicate downstream aggregate

duplicate opportunity acceptance
→ one LeadConnection

duplicate quote acceptance
→ one accepted state

duplicate booking command
→ one booking

duplicate webhook
→ one business effect

worker crash
→ lease expires
→ retry works

disabled integration
→ PENDING_CONFIGURATION

enabled integration
→ safely activates

failed retryable event
→ retried

terminal event
→ visible to Ops

expired hold
→ cannot consume capacity
```

---

# 34. First complete marketplace E2E

Do not call Marketplace V2 MVP finished until this works:

```
```
Customer enters problem
       ↓
ProjectRequest
       ↓
service questionnaire
       ↓
photos
       ↓
location
       ↓
submit
       ↓
qualification
       ↓
matching
       ↓
3 qualified providers
       ↓
opportunities
       ↓
provider accepts
       ↓
LeadConnection
       ↓
conversation
       ↓
quote
       ↓
customer compares
       ↓
customer accepts
       ↓
schedule
       ↓
Booking
       ↓
worker assignment
       ↓
Job
       ↓
completion
       ↓
verified review
```

And prove:

```
```
zero provider case
expired credential case
provider tenant isolation
customer tenant isolation
expired hold
duplicate event
integration failure
payment disabled
```

---

# 35. Feature completion matrix

| AreaCurrentRequired end state |                    |                               |
| ----------------------------- | ------------------ | ----------------------------- |
| Release safety                | In progress        | Complete                      |
| Runtime capabilities          | Started            | Complete authority            |
| ProjectRequest                | Missing            | Core aggregate                |
| Customer request wizard       | Partial/simple     | Full V2 wizard                |
| Provider profiles             | Partial            | Public marketplace profiles   |
| Provider trust                | Partial            | Requirement-driven            |
| Availability                  | Basic              | Rules + exceptions + capacity |
| Matching                      | Partial/conceptual | Deterministic + explainable   |
| Opportunities                 | Missing            | Full state machine            |
| LeadConnection                | Missing            | Controlled connection         |
| Quotes                        | Partial/legacy     | Versioned marketplace quotes  |
| Messaging                     | Missing            | First-class                   |
| Booking                       | Existing           | Downstream outcome            |
| Jobs                          | Existing           | V2 integrated                 |
| Reviews                       | Missing/partial    | Verified jobs only            |
| Provider SaaS                 | Partial            | Full operational portal       |
| Ops                           | Partial            | Command center                |
| Analytics                     | Partial            | Marketplace funnel            |
| Outbox                        | Existing           | Hardened                      |
| Integration inbox             | Missing            | Durable inbound               |
| Codestra                      | Existing boundary  | Formal event integration      |
| Payments                      | Disabled           | Later activation              |
| Payouts                       | Disabled           | Later activation              |
| Subscriptions                 | Missing            | Later provider SaaS           |
| Azure                         | Future             | Modernized platform           |

---

# 36. Definition of technical completion

The system is complete when all of these are true:

```
```
ProjectRequest is authoritative demand model

Matching is deterministic and explainable

Provider eligibility enforces credentials and geography

Opportunity controls customer disclosure

LeadConnection authorizes relationship

Conversation is first-class

Quote is versioned and idempotent

Booking is downstream from accepted work

Job tracks field execution

Review requires completed job

Customer portal works end-to-end

Provider SaaS works end-to-end

Ops can intervene without corrupting history

RBAC is enforced server-side

Outbox is durable

Inbound callbacks are idempotent

Feature capabilities control UI and backend

No disabled feature is advertised

API V1 remains compatible during migration

API V2 is documented and tested

PostgreSQL/PostGIS remains authoritative

Redis only stores disposable state

Codestra/Odoo integrations cannot overwrite marketplace truth

Payments remain gated until independently approved

All migrations pass from current production schema

All quality gates pass
```

---

# 37. Final branch list to hand to the write-enabled developer

```
```
planning/breero-marketplace-v2-unified-architecture

codex/marketplace-v2-release-safety

codex/marketplace-v2-project-requests

codex/marketplace-v2-provider-profiles

codex/marketplace-v2-provider-trust-availability

codex/marketplace-v2-matching

codex/marketplace-v2-opportunities

codex/marketplace-v2-quotes

codex/marketplace-v2-messaging

codex/marketplace-v2-booking-job-bridge

codex/marketplace-v2-customer-experience

codex/marketplace-v2-provider-saas

codex/marketplace-v2-ops-command-center

codex/marketplace-v2-reviews-trust

codex/marketplace-v2-analytics

codex/marketplace-v2-integration-reliability

codex/marketplace-v2-transactions

codex/marketplace-v2-provider-subscriptions

codex/marketplace-v2-azure-modernization
```

## Recommended merge order

```
```
00 Release safety
        ↓
01 ProjectRequest
        ↓
02 Provider profiles
        ↓
03 Trust/availability
        ↓
04 Matching
        ↓
05 Opportunities
        ↓
06 Quotes
        ↓
07 Messaging
        ↓
08 Booking/job bridge
        ↓
09 Customer marketplace
        ↓
10 Provider SaaS
        ↓
11 Ops
        ↓
12 Reviews/trust
        ↓
13 Analytics
        ↓
14 Integration reliability
        ↓
──────── Marketplace MVP ────────
        ↓
15 Transactions
        ↓
16 Subscriptions
        ↓
17 Azure modernization
```

The **planning PR and PR-00 can be opened immediately in parallel**. After that, implementation should move in the order above, with each PR rebased or branched from the latest merged marketplace target. This gives the next write-enabled developer a complete route from the current request-only Breero application to a functioning two-sided services marketplace, without creating another unreviewable mega-PR.
