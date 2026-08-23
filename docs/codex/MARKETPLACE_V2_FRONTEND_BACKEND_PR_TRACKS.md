# BREERO Marketplace V2 — Separate Backend and Frontend PR Tracks

For the implementation, I would now make one important organizational change: **separate backend and frontend PRs completely**. Backend PRs own database, domain logic, endpoints, OpenAPI, events, middleware/outbox and security. Frontend PRs own pages, forms, state, UI, typed client consumption and E2E. That will make review much cleaner.

## Target architecture

Everything revolves around:

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
Booking
      ↓
Job
      ↓
Verified Review
```

A request is not a booking; an opportunity is not a lead connection; a quote acceptance is not an appointment confirmation. That is already the architectural direction recorded in issue #37. 

---

# BACKEND TRACK

Use branch names beginning with:

```
be/marketplace-v2-*
```

No React/Next.js page changes on backend branches.

## BE-01 — ProjectRequest core

Branch:

```
be/marketplace-v2-project-requests
```

Add domain:

```
apps/api/app/domains/project_requests/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── policies.py
├── commands.py
└── events.py
```

Database:

```
project_requests
project_request_answers
project_request_attachments
project_request_status_history
```

Statuses:

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

Fulfillment modes:

```
INSTANT_BOOK
QUOTE_REQUIRED
MANUAL_DISPATCH
UNSERVICEABLE
```

Endpoints:

```
POST   /api/v2/project-requests
GET    /api/v2/project-requests/{id}
PATCH  /api/v2/project-requests/{id}

POST   /api/v2/project-requests/{id}/answers

POST   /api/v2/project-requests/{id}/attachments
DELETE /api/v2/project-requests/{id}/attachments/{attachmentId}

POST   /api/v2/project-requests/{id}/submit
POST   /api/v2/project-requests/{id}/cancel

GET    /api/v2/customer/project-requests
```

Events:

```
project_request.created.v1
project_request.updated.v1
project_request.submitted.v1
project_request.cancelled.v1
project_request.qualified.v1
```

Every mutation:

```
Authorization
Tenant/customer ownership
Idempotency-Key
Request hash
Correlation ID
State validation
Audit
Outbox
```

---

# BE-02 — Service questionnaire/catalog

Branch:

```
be/marketplace-v2-catalog-questionnaire
```

Database:

```
service_categories
services
service_questions
service_question_options
service_question_rules
```

Endpoints:

```
GET /api/v2/catalog/categories
GET /api/v2/catalog/services
GET /api/v2/catalog/services/{slug}
GET /api/v2/catalog/services/{id}/questions
```

Questions must support:

```
TEXT
TEXTAREA
SINGLE_SELECT
MULTI_SELECT
BOOLEAN
NUMBER
DATE
PHOTO
```

Conditional rules:

```
IF answer X
THEN show question Y
```

The backend determines required questions.

Never rely on frontend-only validation.

---

# BE-03 — Provider organization/profile

Branch:

```
be/marketplace-v2-provider-core
```

Database:

```
provider_organizations
provider_profiles
provider_members
provider_workers
provider_services
provider_service_areas
provider_gallery
```

Endpoints:

```
GET /api/v2/providers
GET /api/v2/providers/{slug}
GET /api/v2/providers/{slug}/services
GET /api/v2/providers/{slug}/service-area
GET /api/v2/providers/{slug}/reviews

GET   /api/v2/partner/profile
PATCH /api/v2/partner/profile

GET  /api/v2/partner/services
PUT  /api/v2/partner/services

GET  /api/v2/partner/service-areas
POST /api/v2/partner/service-areas
DELETE /api/v2/partner/service-areas/{id}

GET   /api/v2/partner/workers
POST  /api/v2/partner/workers
PATCH /api/v2/partner/workers/{id}
```

Provider search must never expose:

```
private email
private phone
credential document
identity document
bank/payment details
internal quality notes
```

---

# BE-04 — Provider onboarding

Branch:

```
be/marketplace-v2-provider-onboarding
```

Add:

```
provider_applications
provider_application_status_history
```

Endpoint:

```
POST /api/v2/public/provider-applications
GET  /api/v2/partner/onboarding
PATCH /api/v2/partner/onboarding
POST /api/v2/partner/onboarding/submit
```

Lifecycle:

```
DRAFT
SUBMITTED
UNDER_REVIEW
NEEDS_INFORMATION
APPROVED
REJECTED
```

This form must save to Breero first, then emit an outbox event to middleware.

Never make the public form synchronously depend on Odoo.

---

# BE-05 — Credentials/trust

Branch:

```
be/marketplace-v2-provider-trust
```

Database:

```
credential_requirements
provider_credentials
credential_verifications
provider_documents
```

Statuses:

```
PENDING
VERIFIED
REJECTED
EXPIRED
REVOKED
```

Endpoints:

```
GET  /api/v2/partner/credentials
POST /api/v2/partner/credentials

GET   /api/v2/partner/credentials/{id}
PATCH /api/v2/partner/credentials/{id}

POST /api/v2/partner/credentials/{id}/documents

GET  /api/v2/admin/credentials
POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke
```

Matching must fail closed if a required credential is:

```
missing
expired
revoked
rejected
unverified
```

---

# BE-06 — Availability

Branch:

```
be/marketplace-v2-availability
```

Database:

```
provider_availability_rules
provider_availability_exceptions
worker_availability
```

Endpoints:

```
GET /api/v2/partner/availability
PUT /api/v2/partner/availability

POST   /api/v2/partner/availability/exceptions
DELETE /api/v2/partner/availability/exceptions/{id}

GET /api/v2/providers/{slug}/availability

GET /api/v2/project-requests/{id}/availability
```

Must support:

```
timezone
recurring weekdays
worker availability
blackouts
vacation
capacity
effective ranges
date-specific overrides
```

---

# BE-07 — Matching engine

Branch:

```
be/marketplace-v2-matching
```

Database:

```
matching_runs
match_candidates
match_reasons
```

Eligibility:

```
provider active
service supported
service-area match
credentials valid
insurance valid
not suspended
qualified worker exists
availability exists
capacity exists
```

Ranking:

```
Availability             20
Distance                 20
Verified rating          15
Completion rate          10
Opportunity acceptance   10
Response speed           10
Price competitiveness     5
Previous relationship     5
Quality score             5
```

Endpoints:

```
POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates

GET /api/v2/project-requests/{id}/matches
```

Store every score component.

Operations must be able to answer:

> Why was ABC Plumbing ranked #1?

and:

> Why was XYZ Plumbing rejected?

---

# BE-08 — Opportunities

Branch:

```
be/marketplace-v2-opportunities
```

Database:

```
opportunities
opportunity_status_history
lead_connections
```

States:

```
SENT
VIEWED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN
```

Endpoints:

```
GET /api/v2/partner/opportunities
GET /api/v2/partner/opportunities/{id}

POST /api/v2/partner/opportunities/{id}/view
POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

GET /api/v2/partner/leads

POST /api/v2/ops/project-requests/{id}/opportunities
```

Do not expose customer contact details before LeadConnection policy permits it.

---

# BE-09 — Quotes

Branch:

```
be/marketplace-v2-quotes
```

Database:

```
quotes
quote_versions
quote_line_items
quote_status_history
```

Endpoints:

```
POST /api/v2/partner/project-requests/{id}/quotes

GET   /api/v2/partner/quotes/{id}
PATCH /api/v2/partner/quotes/{id}

POST /api/v2/partner/quotes/{id}/send
POST /api/v2/partner/quotes/{id}/revise
POST /api/v2/partner/quotes/{id}/withdraw

GET /api/v2/project-requests/{id}/quotes
GET /api/v2/quotes/{id}

POST /api/v2/quotes/{id}/accept
POST /api/v2/quotes/{id}/decline
```

Sent quotes become immutable.

Revision:

```
Quote v1
   ↓
revision
   ↓
Quote v2
```

Never edit v1 in place.

---

# BE-10 — Messaging

Branch:

```
be/marketplace-v2-messaging
```

Database:

```
conversations
conversation_participants
messages
message_attachments
message_receipts
```

Endpoints:

```
GET /api/v2/conversations
GET /api/v2/conversations/{id}

GET /api/v2/conversations/{id}/messages

POST /api/v2/conversations/{id}/messages
POST /api/v2/conversations/{id}/attachments

POST /api/v2/conversations/{id}/read
```

Messages:

```
TEXT
IMAGE
DOCUMENT
QUOTE
APPOINTMENT_PROPOSAL
SYSTEM
```

Critical authorization:

```
Provider A
≠
access Provider B conversation
```

---

# BE-11 — Booking bridge

Branch:

```
be/marketplace-v2-booking-bridge
```

Booking becomes downstream from ProjectRequest.

Add:

```
project_request_id
accepted_quote_id
provider_id
worker_id
```

Endpoints:

```
GET /api/v2/bookings/{id}

POST /api/v2/bookings/{id}/confirm
POST /api/v2/bookings/{id}/cancel
POST /api/v2/bookings/{id}/reschedule-request

GET /api/v2/bookings/{id}/timeline
```

If:

```
instant_booking=false
```

then customer-selected timing remains:

```
REQUESTED
```

until confirmed.

---

# BE-12 — Jobs

Branch:

```
be/marketplace-v2-jobs
```

States:

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

Endpoints:

```
GET /api/v2/jobs/{id}
GET /api/v2/jobs/{id}/timeline

POST /api/v2/jobs/{id}/assign
POST /api/v2/jobs/{id}/en-route
POST /api/v2/jobs/{id}/arrive
POST /api/v2/jobs/{id}/start
POST /api/v2/jobs/{id}/complete

POST /api/v2/jobs/{id}/additional-work
POST /api/v2/jobs/{id}/notes
POST /api/v2/jobs/{id}/evidence
```

Never overwrite assignment history.

---

# BE-13 — Reviews

Branch:

```
be/marketplace-v2-reviews
```

Database:

```
reviews
review_dimensions
review_responses
review_moderation
```

Endpoints:

```
POST /api/v2/jobs/{id}/review

GET /api/v2/reviews/{id}

POST /api/v2/partner/reviews/{id}/response

POST /api/v2/admin/reviews/{id}/moderate
```

Eligibility:

```
Job.status == COMPLETED
```

Dimensions:

```
overall
quality
communication
timeliness
value
```

---

# BE-14 — Operations

Branch:

```
be/marketplace-v2-operations
```

Endpoints:

```
GET /api/v2/ops/project-requests

GET /api/v2/ops/project-requests/{id}

GET /api/v2/ops/jobs
GET /api/v2/ops/jobs/{id}

POST /api/v2/ops/jobs/{id}/assign

GET /api/v2/ops/providers

GET /api/v2/ops/exceptions

GET /api/v2/ops/integration-failures

POST /api/v2/ops/integration-events/{id}/retry
```

Ops exception types:

```
NO_MATCH
STALE_OPPORTUNITY
NO_PROVIDER_RESPONSE
QUOTE_OVERDUE
CREDENTIAL_EXPIRING
CREDENTIAL_EXPIRED
SCHEDULING_CONFLICT
UNASSIGNED_JOB
LATE_JOB
INTEGRATION_FAILURE
```

---

# BE-15 — Admin/RBAC

Branch:

```
be/marketplace-v2-admin-rbac
```

Canonical roles:

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

Endpoints:

```
GET /api/v2/admin/users
GET /api/v2/admin/roles

PUT /api/v2/admin/users/{id}/roles

GET /api/v2/admin/providers

POST /api/v2/admin/providers/{id}/approve
POST /api/v2/admin/providers/{id}/suspend

GET /api/v2/admin/audit-events

GET /api/v2/admin/features
PUT /api/v2/admin/features/{key}
```

Feature entitlement and RBAC are separate concepts.

---

# BE-16 — Integration/outbox/inbox

Branch:

```
be/marketplace-v2-integrations
```

This is how every important form connects to middleware.

The correct design is **not**:

```
Browser
 ↓
Codestra middleware
```

It is:

```
Browser
 ↓
Breero API
 ↓
Breero PostgreSQL
 + Outbox Event
 ↓
COMMIT
 ↓
Worker
 ↓
Codestra/Kong
```

This keeps Breero authoritative.

Issue #37 already defines Codestra/Kong as the protected integration boundary, Odoo as a CRM projection, n8n as approved orchestration only, Klyrow as email delivery and Telnexa as SMS delivery. 

## Outbox

States:

```
PENDING_CONFIGURATION
PENDING
PROCESSING
RETRYABLE
DELIVERED
FAILED_TERMINAL
```

## Inbox

Add:

```
integration_inbox
```

Unique:

```
(provider, external_event_id)
```

Inbound sources:

```
Codestra
Klyrow
Telnexa
Odoo acknowledgements
n8n callbacks
Stripe later
```

Every inbound event:

```
authenticate
verify signature
check timestamp
check replay
deduplicate
authorize tenant
process idempotently
audit
```

---

# Form-to-middleware mapping

This is particularly important for your requirement that **all forms work and connect correctly to middleware**.

| Form | BREERO API | BREERO data | Outbox event |
|---|---|---|---|
| Customer service request        | `POST /api/v2/project-requests` + `/submit` | ProjectRequest      | `project_request.submitted.v1`        |
| Provider application            | `POST /api/v2/public/provider-applications` | ProviderApplication | `provider_application.submitted.v1`   |
| Quote submission                | `/partner/.../quotes/{id}/send`             | Quote               | `quote.sent.v1`                       |
| Customer accepts quote          | `/quotes/{id}/accept`                       | Quote               | `quote.accepted.v1`                   |
| Message                         | `/conversations/{id}/messages`              | Message             | `conversation.message_sent.v1`        |
| Booking confirmation            | `/bookings/{id}/confirm`                    | Booking             | `booking.confirmed.v1`                |
| Job completion                  | `/jobs/{id}/complete`                       | Job                 | `job.completed.v1`                    |
| Review                          | `/jobs/{id}/review`                         | Review              | `review.submitted.v1`                 |
| Credential upload               | `/partner/credentials`                      | Credential          | `credential.submitted.v1`             |
| Provider approved               | `/admin/providers/{id}/approve`             | Provider            | `provider.approved.v1`                |
| Communication preference        | compliance endpoint                         | Consent             | `communication.preference_changed.v1` |
| Contact/support                 | `/api/v2/public/contact-requests`           | ContactRequest      | `contact_request.created.v1`          |

The **browser gets success when Breero durably commits**, not when Odoo/email/SMS happens.

---

# FRONTEND TRACK

Use:

```
fe/marketplace-v2-*
```

Frontend branches do **not** add migrations or change backend domain behavior.

They consume OpenAPI and typed clients.

---

# FE-01 — Shared V2 API client

Branch:

```
fe/marketplace-v2-api-client
```

Update:

```
packages/types
packages/api-client
packages/ui
```

Generate/define typed interfaces for:

```
ProjectRequest
ProviderProfile
Match
Opportunity
LeadConnection
Quote
Conversation
Message
Booking
Job
Review
Credential
Availability
```

All UI calls go through:

```
@breero/api-client
```

Do not scatter raw `fetch()` calls throughout components.

---

# FE-02 — Design system

Branch:

```
fe/marketplace-v2-design-system
```

Components:

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

Required states:

```
loading
empty
error
disabled
success
permission denied
offline/retry
```

---

# FE-03 — Customer homepage/search

Branch:

```
fe/marketplace-v2-home
```

Hero:

```
What do you need help with?

[ My kitchen sink is leaking... ]

[ ZIP code ] [ Find professionals ]
```

Then:

```
Plumbing
Electrical
HVAC
Cleaning
Handyman
Roofing
Landscaping
Appliances
```

Runtime capabilities determine CTAs.

---

# FE-04 — ProjectRequest wizard

Branch:

```
fe/marketplace-v2-request-wizard
```

Steps:

```
1 Service
2 Questions
3 Description
4 Photos
5 Address/property
6 Urgency
7 Preferred timing
8 Review
9 Submit
```

Must support:

```
save draft
resume draft
back/forward
conditional questions
file upload
validation
server errors
idempotent submit
mobile
keyboard
screen reader
```

No direct middleware call.

Use Breero V2 API.

---

# FE-05 — Customer matches/provider discovery

Branch:

```
fe/marketplace-v2-provider-discovery
```

Pages:

```
/pros
/pros/{slug}
/requests/{id}/matches
```

Provider card:

```
name
photo/logo
rating
verified jobs
verified badges
service summary
distance
response time
```

Do not show private provider data.

---

# FE-06 — Customer quote comparison

Branch:

```
fe/marketplace-v2-customer-quotes
```

Page:

```
/requests/{id}/quotes
```

Compare:

```
provider
rating
total
line items
availability
valid-until
credentials
response time
```

Actions:

```
Message
Accept
Decline
```

---

# FE-07 — Customer messaging

Branch:

```
fe/marketplace-v2-customer-messaging
```

Pages:

```
/messages
/messages/{conversationId}
```

Support:

```
text
image
document
quote card
appointment proposal
system event
```

---

# FE-08 — Customer account

Branch:

```
fe/marketplace-v2-customer-account
```

Navigation:

```
Requests
Quotes
Messages
Bookings
Jobs
Reviews
Properties
Profile
```

---

# FE-09 — Provider onboarding

Branch:

```
fe/marketplace-v2-provider-onboarding
```

Form:

```
Company
Owner
Services
Service area
Licenses
Insurance
Workers
Availability
Documents
Review
Submit
```

Autosave draft.

Uploads direct to controlled Breero storage URLs—not arbitrary public buckets.

---

# FE-10 — Provider dashboard

Branch:

```
fe/marketplace-v2-provider-dashboard
```

Navigation:

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
Settings
```

---

# FE-11 — Provider opportunity inbox

Branch:

```
fe/marketplace-v2-provider-opportunities
```

Show:

```
service
approximate area
distance
urgency
requested time
match strength
job summary
```

Actions:

```
View
Accept
Decline
```

No full customer PII before LeadConnection.

---

# FE-12 — Quote builder

Branch:

```
fe/marketplace-v2-provider-quotes
```

Provider form:

```
Labor
Materials
Other items
Taxes
Discount
Notes
Validity
Availability
```

Features:

```
save draft
preview
send
revise
withdraw
```

---

# FE-13 — Provider messaging

Branch:

```
fe/marketplace-v2-provider-messaging
```

Same shared conversation component.

Authorization remains backend authority.

---

# FE-14 — Provider schedule/jobs

Branch:

```
fe/marketplace-v2-provider-jobs
```

Views:

```
day
week
list
```

Job actions:

```
Accept assignment
En route
Arrived
Start
Additional work
Complete
```

---

# FE-15 — Provider workers/availability

Branch:

```
fe/marketplace-v2-provider-workforce
```

Forms:

```
Add worker
Edit worker
Skills
Credentials
Working hours
Exceptions
Vacation
Capacity
```

---

# FE-16 — Provider credentials

Branch:

```
fe/marketplace-v2-provider-credentials
```

Show:

```
Verified
Pending
Expiring
Expired
Rejected
Revoked
```

Forms:

```
credential type
number
jurisdiction
effective date
expiration
document
```

---

# FE-17 — Operations console

Branch:

```
fe/marketplace-v2-ops
```

Main navigation:

```
Requests
Matching
Jobs
Providers
Exceptions
Integrations
Map
```

Matching inspector:

```
ABC Plumbing
Eligible: YES
Distance: 2.1mi
Availability: YES
Credentials: PASS
Score: 94

Availability       20/20
Distance           19/20
Rating             14/15
Completion          9/10
Acceptance          9/10
Response            9/10
...
```

Rejected candidate:

```
XYZ Services
Eligible: NO

LICENSE_EXPIRED
```

---

# FE-18 — Admin console

Branch:

```
fe/marketplace-v2-admin
```

Pages:

```
Providers
Credential review
Users
Roles
Feature flags
Audit
Integration failures
```

---

# FE-19 — Reviews UI

Branch:

```
fe/marketplace-v2-reviews
```

Customer form after completed job:

```
Overall          ★★★★★
Quality          ★★★★★
Communication    ★★★★★
Timeliness       ★★★★★
Value            ★★★★★

Tell us about your experience
```

Provider response.

Admin moderation.

---

# Frontend forms that must be tested

Every form requires:

```
happy path
validation failure
server failure
401
403
409 conflict
422 validation
429 rate limit
500 retry state
network timeout
double-click submission
mobile
keyboard
screen reader
```

Critical forms:

```
Login
Registration
Forgot/reset password

Project request
Address
Service questions
Photo upload

Provider application
Provider profile
Worker
Service areas
Availability
Credentials

Opportunity accept/decline

Quote create/revise/send
Quote accept/decline

Message composer

Booking reschedule/cancel

Job status commands

Review

Communication preferences
Contact/support

Admin provider approval
Credential approval
Feature toggle
Manual retry
```

---

# Separate frontend/backend dependency order

This is the cleanest sequence.

```
BE-01 ProjectRequest
       ↓
FE-01 Typed V2 client
       ↓
FE-04 Request wizard

BE-02 Catalog
       ↓
FE-03 Homepage/search

BE-03 Provider
BE-05 Trust
BE-06 Availability
       ↓
FE-05 Provider discovery

BE-07 Matching
       ↓
BE-08 Opportunities
       ↓
FE-11 Provider opportunities
       ↓
FE-17 Ops matching

BE-09 Quotes
       ↓
FE-12 Provider quote builder
       ↓
FE-06 Customer quote comparison

BE-10 Messaging
       ↓
FE-07 Customer messaging
FE-13 Provider messaging

BE-11 Booking
BE-12 Jobs
       ↓
FE-14 Provider jobs
FE-08 Customer jobs

BE-13 Reviews
       ↓
FE-19 Reviews

BE-16 Integrations
       ↓
middleware certification
```

---

# Important Git rule

Do not make frontend branch depend on an unmerged backend branch for weeks.

Preferred process:

```
Backend PR
    ↓
review
    ↓
merge
    ↓
Frontend branch from new target
    ↓
frontend PR
```

For UI work that must begin earlier, use mocked typed contracts but rebase and run real API E2E before merge.

---

# Middleware connection architecture

This should be mandatory for all marketplace integration work.

```
USER FORM
    ↓
Next.js
    ↓
Breero FastAPI
    ↓
DOMAIN SERVICE
    ↓
PostgreSQL
    +
Transactional Outbox
    ↓
COMMIT
    ↓
Worker
    ↓
Codestra/Kong
    ↓
┌─────────────┬──────────────┬──────────────┐
Odoo         Klyrow         Telnexa        n8n
CRM          Email          SMS            approved workflow
```

External systems must never directly modify:

```
ProjectRequest
Match
Opportunity
LeadConnection
Quote
Booking
Job
Review
```

Issue #37 already establishes this source-of-truth boundary. 

---

# Middleware events to implement

```
project_request.submitted.v1
project_request.cancelled.v1

provider_application.submitted.v1
provider.approved.v1
provider.suspended.v1

opportunity.sent.v1
opportunity.accepted.v1

lead.connected.v1

quote.sent.v1
quote.accepted.v1

conversation.message_sent.v1

booking.created.v1
booking.confirmed.v1
booking.cancelled.v1

job.assigned.v1
job.en_route.v1
job.completed.v1

review.submitted.v1

credential.submitted.v1
credential.verified.v1
credential.expiring.v1
credential.expired.v1
```

Every event needs:

```
event_id
event_type
schema_version
occurred_at

aggregate_type
aggregate_id
aggregate_version

correlation_id
causation_id

legal_entity_id
tenant_id

payload
```

---

# Middleware failure behavior

Never lose customer requests because Codestra/Odoo/email is down.

Example:

```
Customer clicks Submit
       ↓
ProjectRequest saved
       ↓
Outbox saved
       ↓
DB COMMIT
       ↓
Customer gets:
"Request received"
       ↓
Codestra unavailable
       ↓
outbox = RETRYABLE
       ↓
retry later
```

Not:

```
Codestra failed
→ customer loses request
```

---

# Middleware delivery state

```
PENDING_CONFIGURATION
PENDING
PROCESSING
RETRYABLE
DELIVERED
FAILED_TERMINAL
```

Operations UI needs to display each failure.

---

# Payments — keep separate

Do not mix Stripe into the marketplace core.

Later backend:

```
be/marketplace-v2-payments
```

Later frontend:

```
fe/marketplace-v2-payments
```

Current flags remain false, consistent with PR #35 and the implementation mission. 

---

# Required backend CI per PR

```
Ruff
compileall
pytest

PostgreSQL/PostGIS integration tests

Alembic upgrade
schema drift
practical downgrade where safe

authorization tests
negative authorization tests

state-transition tests

idempotency tests
concurrency tests

OpenAPI generation
API compatibility

outbox tests where applicable
```

Issue #37 already requires migrations, PostgreSQL/PostGIS integration, auth/negative-auth, idempotency/concurrency, OpenAPI and retry/lease tests per implementation PR. 

---

# Required frontend CI per PR

```
ESLint
TypeScript

unit tests
component tests

API-client tests

accessibility
responsive tests

Playwright:
Chromium
Firefox
WebKit

375
430
768
1024
1280
1440

production Next.js build
```

PR #35 demonstrated this exact kind of browser/viewport gate with 255 Playwright tests passing after the capability-fixture repair. 

---

# Marketplace completion E2E

Do not mark Marketplace V2 complete until the real applications prove:

```
Customer
 ↓
ProjectRequest
 ↓
questions
 ↓
photos
 ↓
address
 ↓
submit
 ↓
qualification
 ↓
matching
 ↓
3 eligible providers
 ↓
opportunities
 ↓
provider accepts
 ↓
LeadConnection
 ↓
conversation
 ↓
provider builds quote
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
Verified Review
```

This is also the completion sequence in the existing implementation mission. 

And E2E must prove:

```
zero provider
expired credential
suspended provider
invalid service area

Provider A cannot access Provider B data
Customer A cannot access Customer B request

expired hold
double-click
duplicate command
duplicate event

worker crash
lease recovery

Codestra offline
Klyrow offline
Telnexa offline

payments disabled
```

---

## The resulting separation

Your GitHub will end up looking roughly like this:

```
BACKEND
───────
be/marketplace-v2-project-requests
be/marketplace-v2-catalog-questionnaire
be/marketplace-v2-provider-core
be/marketplace-v2-provider-onboarding
be/marketplace-v2-provider-trust
be/marketplace-v2-availability
be/marketplace-v2-matching
be/marketplace-v2-opportunities
be/marketplace-v2-quotes
be/marketplace-v2-messaging
be/marketplace-v2-booking-bridge
be/marketplace-v2-jobs
be/marketplace-v2-reviews
be/marketplace-v2-operations
be/marketplace-v2-admin-rbac
be/marketplace-v2-integrations


FRONTEND
────────
fe/marketplace-v2-api-client
fe/marketplace-v2-design-system
fe/marketplace-v2-home
fe/marketplace-v2-request-wizard
fe/marketplace-v2-provider-discovery
fe/marketplace-v2-customer-quotes
fe/marketplace-v2-customer-messaging
fe/marketplace-v2-customer-account
fe/marketplace-v2-provider-onboarding
fe/marketplace-v2-provider-dashboard
fe/marketplace-v2-provider-opportunities
fe/marketplace-v2-provider-quotes
fe/marketplace-v2-provider-messaging
fe/marketplace-v2-provider-jobs
fe/marketplace-v2-provider-workforce
fe/marketplace-v2-provider-credentials
fe/marketplace-v2-ops
fe/marketplace-v2-admin
fe/marketplace-v2-reviews
```

That is the structure I would give the write-enabled implementation agent. It keeps **database/API/domain/middleware work entirely backend**, keeps **pages/forms/design entirely frontend**, and connects them through a typed `/api/v2` contract. It also preserves the current safety rule that simply adding an endpoint or schema must not turn on a production capability.
