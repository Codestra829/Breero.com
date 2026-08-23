# BREERO Marketplace V2 — Complete Backend Implementation Authority

## Status and safety boundary

This is documentation-only implementation authority for the BREERO repository. It must not be deployed. Complete and human-merge PR-00 release safety and the Marketplace V2 architecture authority before creating implementation branches from the latest merged target.

The current request-only/manual-dispatch behavior remains authoritative. Payments, payouts, paid leads, provider self-service, marketplace matching, messaging, reviews, instant booking, automatic assignment, automatic confirmation, marketing, unrestricted email/SMS and external automation remain disabled until separately implemented, tested and authorized.
## 1. Purpose

This document is the backend implementation authority for BREERO Marketplace V2.

Backend owns:

- PostgreSQL/PostGIS schema
- Alembic migrations
- FastAPI routers
- domain services
- repositories/queries
- commands
- state machines
- authorization
- tenant/provider boundaries
- idempotency
- matching
- scheduling
- credentials
- quotes
- messaging persistence
- booking/job orchestration
- reviews
- operations APIs
- admin APIs
- transactional outbox
- integration inbox
- Codestra/Kong connectivity
- middleware delivery
- observability
- backend tests
- OpenAPI

Backend does **not** own React/Next.js page implementation.

---

# 2. Mandatory architecture

Use:

```text
Router
  ↓
Domain Service / Command
  ↓
Repository / Query
  ↓
Async SQLAlchemy
  ↓
PostgreSQL/PostGIS

```

PostgreSQL/PostGIS is authoritative.

Redis is disposable only:

```text
cache
rate limits
short-lived locks
Celery/worker state
availability cache
matching cache

```

Do not store authoritative marketplace state in Redis.

---

# 3. Marketplace lifecycle

Canonical lifecycle:

```text
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

```text
ProjectRequest = customer demand
Matching       = eligibility + ranking
Opportunity    = controlled invitation
LeadConnection = authorized customer/provider relationship
Quote          = commercial proposal
Booking        = scheduling outcome
Job            = field execution
Review         = completed-job trust signal

```

Never move qualification, provider search, quoting or communication into Booking.

---

# 4. Backend branch plan

After release-safety and architecture authority are human merged, use separate backend PRs.

```text
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
be/marketplace-v2-analytics
be/marketplace-v2-transactions
be/marketplace-v2-subscriptions

```

One Draft PR per branch.

Do not build one mega-PR.

---

# 5. Backend repository structure

Target:

```text
apps/api/app/

├── api/
│   ├── v1/
│   └── v2/
│       ├── router.py
│       ├── public.py
│       ├── catalog.py
│       ├── project_requests.py
│       ├── providers.py
│       ├── customer.py
│       ├── partner.py
│       ├── workers.py
│       ├── matching.py
│       ├── opportunities.py
│       ├── quotes.py
│       ├── conversations.py
│       ├── bookings.py
│       ├── jobs.py
│       ├── reviews.py
│       ├── operations.py
│       ├── admin.py
│       ├── analytics.py
│       └── integrations.py
│
├── domains/
│   ├── project_requests/
│   ├── catalog/
│   ├── providers/
│   ├── provider_onboarding/
│   ├── credentials/
│   ├── availability/
│   ├── matching/
│   ├── opportunities/
│   ├── quotes/
│   ├── conversations/
│   ├── booking/
│   ├── jobs/
│   ├── reviews/
│   ├── operations/
│   ├── analytics/
│   ├── payments/
│   ├── subscriptions/
│   ├── compliance/
│   ├── integrations/
│   ├── audit/
│   └── common/
│
├── workers/
├── core/
└── config.py

```

Each domain normally owns:

```text
models.py
schemas.py
repository.py
service.py
commands.py
policies.py
events.py
queries.py

```

Reuse existing conventions instead of mechanically creating unused files.

---

# 6. Shared command requirements

Every externally retryable state-changing command requires:

```text
Authenticated actor
Tenant/legal-entity context
Permission
Ownership validation
Idempotency-Key
Request hash
Correlation ID
Expected/current aggregate version
Explicit state transition
Audit entry
Outbox event
Atomic commit

```

Suggested common context:

```python
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class CommandContext:
    actor_id: UUID
    tenant_id: UUID | None
    legal_entity_id: UUID | None
    idempotency_key: str
    request_hash: str
    correlation_id: str

```

---

# 7. API V2 router

Keep V1 compatible.

Add:

```python
from fastapi import APIRouter

from . import (
    admin,
    analytics,
    bookings,
    catalog,
    conversations,
    customer,
    integrations,
    jobs,
    matching,
    opportunities,
    operations,
    partner,
    project_requests,
    providers,
    public,
    quotes,
    reviews,
    workers,
)

api_v2 = APIRouter()

api_v2.include_router(public.router, prefix="/public")
api_v2.include_router(catalog.router, prefix="/catalog")
api_v2.include_router(project_requests.router, prefix="/project-requests")
api_v2.include_router(providers.router, prefix="/providers")
api_v2.include_router(customer.router, prefix="/customer")
api_v2.include_router(partner.router, prefix="/partner")
api_v2.include_router(workers.router, prefix="/worker")
api_v2.include_router(matching.router, prefix="/matching")
api_v2.include_router(opportunities.router, prefix="/opportunities")
api_v2.include_router(quotes.router, prefix="/quotes")
api_v2.include_router(conversations.router, prefix="/conversations")
api_v2.include_router(bookings.router, prefix="/bookings")
api_v2.include_router(jobs.router, prefix="/jobs")
api_v2.include_router(reviews.router, prefix="/reviews")
api_v2.include_router(operations.router, prefix="/ops")
api_v2.include_router(admin.router, prefix="/admin")
api_v2.include_router(analytics.router, prefix="/analytics")
api_v2.include_router(integrations.router, prefix="/integrations")

```

Mount at:

```text
/api/v2

```

---

# 8. Database — identity/customer foundation

Reuse existing user/auth schema where possible.

Add or normalize:

## customer\_profiles

```text
id UUID PK
user_id UUID UNIQUE
first_name
last_name
display_name
primary_phone
primary_email
timezone
created_at
updated_at

```

## customer\_properties

```text
id UUID PK
customer_id UUID FK
name
property_type
year_built nullable
square_feet nullable
bedrooms nullable
bathrooms nullable
active
created_at
updated_at

```

## addresses

Preserve existing address model.

Required:

```text
id
customer_id nullable
property_id nullable
line1
line2
city
region
postal_code
country_code
latitude
longitude
timezone_name
geocode_status
created_at
updated_at

```

PostGIS point/geography should be available for distance calculations.

---

# 9. ProjectRequest schema

## project\_requests

```text
id UUID PK
reference VARCHAR UNIQUE

customer_id UUID NULL
property_id UUID NULL
service_id UUID FK
address_id UUID FK
legal_entity_id UUID NULL

status VARCHAR
fulfillment_mode VARCHAR NULL

title VARCHAR NULL
description TEXT
urgency VARCHAR

budget_min_minor BIGINT NULL
budget_max_minor BIGINT NULL
currency CHAR(3)

preferred_start_at TIMESTAMPTZ NULL
preferred_end_at TIMESTAMPTZ NULL

source VARCHAR
source_campaign VARCHAR NULL

submitted_at TIMESTAMPTZ NULL
expires_at TIMESTAMPTZ NULL
cancelled_at TIMESTAMPTZ NULL

version INTEGER NOT NULL DEFAULT 1

created_at
updated_at

```

States:

```text
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

```text
INSTANT_BOOK
QUOTE_REQUIRED
MANUAL_DISPATCH
UNSERVICEABLE

```

## project\_request\_answers

```text
id
project_request_id
question_id
answer_json JSONB
created_at
updated_at

```

Unique:

```text
(project_request_id, question_id)

```

## project\_request\_attachments

```text
id
project_request_id
storage_key
original_filename
content_type
size_bytes
checksum_sha256
scan_status
created_by
created_at

```

## project\_request\_status\_history

```text
id
project_request_id
from_status
to_status
reason_code
actor_id
metadata_json
created_at

```

---

# 10. ProjectRequest API

Public/customer:

```http
POST   /api/v2/project-requests
GET    /api/v2/project-requests/{id}
PATCH  /api/v2/project-requests/{id}

PUT    /api/v2/project-requests/{id}/answers/{questionId}
DELETE /api/v2/project-requests/{id}/answers/{questionId}

POST   /api/v2/project-requests/{id}/attachments
DELETE /api/v2/project-requests/{id}/attachments/{attachmentId}

POST   /api/v2/project-requests/{id}/submit
POST   /api/v2/project-requests/{id}/cancel

GET    /api/v2/customer/project-requests

```

Operations:

```http
GET  /api/v2/ops/project-requests
GET  /api/v2/ops/project-requests/{id}
POST /api/v2/ops/project-requests/{id}/qualify
POST /api/v2/ops/project-requests/{id}/mark-unserviceable

```

Example create router:

```python
@router.post("", response_model=ProjectRequestView, status_code=201)
async def create_project_request(
    payload: ProjectRequestCreate,
    request: Request,
    user: UserContext = Depends(require_customer_or_guest),
    session: AsyncSession = Depends(get_session),
):
    context = command_context(request, user)
    return await ProjectRequestService(session).create(payload, context)

```

---

# 11. Catalog/questionnaire schema

## service\_categories

```text
id
slug
name
description
sort_order
active

```

## services

Preserve existing table and extend only when needed.

Recommended fields:

```text
id
category_id
slug
name
description
active
is_bookable
default_fulfillment_mode
requires_provider_quote
minimum_notice_minutes

```

## service\_questions

```text
id
service_id
key
label
help_text
question_type
required
sort_order
active
validation_json

```

Question types:

```text
TEXT
TEXTAREA
BOOLEAN
NUMBER
SINGLE_SELECT
MULTI_SELECT
DATE
TIME
PHOTO

```

## service\_question\_options

```text
id
question_id
value
label
sort_order
active

```

## service\_question\_rules

```text
id
service_id
source_question_id
operator
expected_value_json
target_question_id
action

```

Actions:

```text
SHOW
HIDE
REQUIRE
OPTIONAL

```

---

# 12. Catalog APIs

```http
GET /api/v2/catalog/categories
GET /api/v2/catalog/categories/{slug}

GET /api/v2/catalog/services
GET /api/v2/catalog/services/{slug}
GET /api/v2/catalog/services/{id}/questions

```

Admin:

```http
POST   /api/v2/admin/catalog/categories
PATCH  /api/v2/admin/catalog/categories/{id}

POST   /api/v2/admin/catalog/services
PATCH  /api/v2/admin/catalog/services/{id}

POST   /api/v2/admin/catalog/services/{id}/questions
PATCH  /api/v2/admin/catalog/questions/{id}
DELETE /api/v2/admin/catalog/questions/{id}

```

---

# 13. Provider schema

## provider\_organizations

```text
id
legal_name
display_name
slug UNIQUE
entity_type
tax_country
status
website
primary_email
primary_phone
timezone
created_at
updated_at

```

Provider states:

```text
DRAFT
PENDING_REVIEW
ACTIVE
SUSPENDED
REJECTED
CLOSED

```

## provider\_profiles

```text
provider_id PK/FK
headline
description
years_in_business
logo_storage_key
cover_storage_key
response_time_minutes nullable
verified_jobs_count
rating_average
rating_count
public_profile_enabled
updated_at

```

## provider\_members

```text
id
provider_id
user_id
role
status
created_at

```

## provider\_workers

```text
id
provider_id
user_id nullable
first_name
last_name
phone
email
status
hire_date nullable
created_at
updated_at

```

## provider\_services

```text
provider_id
service_id
active
starting_price_minor nullable
currency
created_at
updated_at

```

Unique:

```text
(provider_id, service_id)

```

## provider\_service\_areas

```text
id
provider_id
service_id nullable
area_type
geometry/geography
radius_meters nullable
active
created_at

```

Use GiST indexes.

---

# 14. Public provider APIs

```http
GET /api/v2/providers
GET /api/v2/providers/{slug}

GET /api/v2/providers/{slug}/services
GET /api/v2/providers/{slug}/reviews
GET /api/v2/providers/{slug}/service-area
GET /api/v2/providers/{slug}/availability-summary

```

Filters:

```text
service
postal_code
latitude/longitude
rating
verified
availability
distance

```

Never expose private provider/member/credential-document data.

---

# 15. Provider portal APIs

Profile:

```http
GET   /api/v2/partner/profile
PATCH /api/v2/partner/profile

```

Services:

```http
GET /api/v2/partner/services
PUT /api/v2/partner/services

```

Service areas:

```http
GET    /api/v2/partner/service-areas
POST   /api/v2/partner/service-areas
PATCH  /api/v2/partner/service-areas/{id}
DELETE /api/v2/partner/service-areas/{id}

```

Workers:

```http
GET    /api/v2/partner/workers
POST   /api/v2/partner/workers
GET    /api/v2/partner/workers/{id}
PATCH  /api/v2/partner/workers/{id}
POST   /api/v2/partner/workers/{id}/activate
POST   /api/v2/partner/workers/{id}/deactivate

```

---

# 16. Provider onboarding schema

## provider\_applications

```text
id
user_id nullable
legal_name
display_name
contact_first_name
contact_last_name
email
phone
website nullable
status
submission_json
submitted_at nullable
reviewed_at nullable
reviewed_by nullable
version
created_at
updated_at

```

States:

```text
DRAFT
SUBMITTED
UNDER_REVIEW
NEEDS_INFORMATION
APPROVED
REJECTED

```

## provider\_application\_status\_history

```text
id
application_id
from_status
to_status
reason
actor_id nullable
created_at

```

---

# 17. Provider onboarding APIs

Public:

```http
POST /api/v2/public/provider-applications

```

Applicant:

```http
GET   /api/v2/partner/onboarding
PATCH /api/v2/partner/onboarding
POST  /api/v2/partner/onboarding/submit

```

Admin:

```http
GET  /api/v2/admin/provider-applications
GET  /api/v2/admin/provider-applications/{id}

POST /api/v2/admin/provider-applications/{id}/request-information
POST /api/v2/admin/provider-applications/{id}/approve
POST /api/v2/admin/provider-applications/{id}/reject

```

Every submitted application emits:

```text
provider_application.submitted.v1

```

to the outbox.

---

# 18. Credentials/trust schema

## credential\_requirements

```text
id
service_id nullable
jurisdiction
credential_type
subject_type
required
verification_mode
active
created_at

```

Subject:

```text
PROVIDER
WORKER

```

## provider\_credentials

```text
id
provider_id
worker_id nullable
credential_type
credential_number_ciphertext
credential_number_last4
issuing_authority
jurisdiction
effective_at nullable
expires_at nullable
status
document_id nullable
created_at
updated_at

```

States:

```text
PENDING
VERIFIED
REJECTED
EXPIRED
REVOKED

```

## credential\_verifications

```text
id
credential_id
status
verification_source
reviewer_id nullable
reason_code nullable
metadata_json
verified_at

```

## provider\_documents

```text
id
provider_id
worker_id nullable
document_type
storage_key
content_type
checksum
scan_status
created_at

```

---

# 19. Credential APIs

Provider:

```http
GET    /api/v2/partner/credentials
POST   /api/v2/partner/credentials

GET    /api/v2/partner/credentials/{id}
PATCH  /api/v2/partner/credentials/{id}

POST   /api/v2/partner/credentials/{id}/documents
DELETE /api/v2/partner/credentials/{id}/documents/{documentId}

```

Admin/trust:

```http
GET  /api/v2/admin/credentials
GET  /api/v2/admin/credentials/{id}

POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke

```

Matching fails closed for required credentials.

---

# 20. Availability schema

## provider\_availability\_rules

```text
id
provider_id
worker_id nullable
weekday
start_time
end_time
capacity
timezone
effective_from
effective_until nullable
active

```

## provider\_availability\_exceptions

```text
id
provider_id
worker_id nullable
date
start_time nullable
end_time nullable
capacity_override nullable
unavailable boolean
reason

```

No universal 07:00–19:00 assumption.

---

# 21. Availability APIs

Provider:

```http
GET /api/v2/partner/availability
PUT /api/v2/partner/availability

POST   /api/v2/partner/availability/exceptions
PATCH  /api/v2/partner/availability/exceptions/{id}
DELETE /api/v2/partner/availability/exceptions/{id}

```

Worker:

```http
GET /api/v2/worker/availability
PUT /api/v2/worker/availability

```

Marketplace:

```http
GET /api/v2/providers/{slug}/availability-summary
GET /api/v2/project-requests/{id}/availability

```

---

# 22. Matching schema

## matching\_runs

```text
id
project_request_id
algorithm
algorithm_version
configuration_json
status
started_at
completed_at
created_by nullable

```

## match\_candidates

```text
id
matching_run_id
provider_id
eligible
rank nullable
score nullable
distance_meters nullable
availability_score nullable
distance_score nullable
rating_score nullable
completion_score nullable
acceptance_score nullable
response_score nullable
price_score nullable
relationship_score nullable
quality_score nullable
created_at

```

## match\_reasons

```text
id
candidate_id
reason_type
reason_code
passed
score_delta nullable
detail_json

```

---

# 23. Matching policy

Hard filters:

```text
provider active
service supported
geography supported
credentials valid
required insurance valid
provider not suspended
worker qualification available
availability available
capacity available
legal entity compatible

```

Ranking weights V1:

```text
Availability             20
Distance                 20
Verified rating          15
Completion rate          10
Opportunity acceptance   10
Response speed           10
Price competitiveness     5
Prior relationship        5
Breero quality score      5

```

Do not use ML initially.

---

# 24. Matching APIs

Ops:

```http
POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates
GET /api/v2/ops/matching-runs/{id}/candidates/{candidateId}

```

Customer-safe projection:

```http
GET /api/v2/project-requests/{id}/matches

```

Do not reveal internal rejection/quality data publicly.

---

# 25. Opportunities schema

## opportunities

```text
id
project_request_id
provider_id
matching_run_id
candidate_id
status
sent_at
viewed_at nullable
responded_at nullable
expires_at
version
created_at
updated_at

```

States:

```text
SENT
VIEWED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN

```

## opportunity\_status\_history

```text
id
opportunity_id
from_status
to_status
reason
actor_id nullable
created_at

```

## lead\_connections

```text
id
project_request_id
provider_id
opportunity_id
status
customer_contact_access_level
connected_at
closed_at nullable
created_at

```

---

# 26. Opportunity APIs

Provider:

```http
GET /api/v2/partner/opportunities
GET /api/v2/partner/opportunities/{id}

POST /api/v2/partner/opportunities/{id}/view
POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

GET /api/v2/partner/leads
GET /api/v2/partner/leads/{id}

```

Ops:

```http
POST /api/v2/ops/project-requests/{id}/opportunities
POST /api/v2/ops/opportunities/{id}/withdraw

```

Customer PII is minimized until LeadConnection authorizes access.

---

# 27. Quote schema

## quotes

```text
id
project_request_id
lead_connection_id
provider_id
current_version_id nullable
status
currency
created_at
updated_at

```

## quote\_versions

```text
id
quote_id
version_number
subtotal_minor
tax_minor
discount_minor
fee_minor
total_minor
notes
valid_until
created_by
created_at
sent_at nullable

```

## quote\_line\_items

```text
id
quote_version_id
type
description
quantity NUMERIC
unit_price_minor BIGINT
amount_minor BIGINT
sort_order

```

Types:

```text
LABOR
MATERIAL
TRAVEL
PERMIT
OTHER
DISCOUNT

```

## quote\_status\_history

```text
id
quote_id
from_status
to_status
quote_version_id
actor_id
created_at

```

States:

```text
DRAFT
SENT
REVISED
ACCEPTED
DECLINED
EXPIRED
WITHDRAWN

```

---

# 28. Quote APIs

Provider:

```http
POST /api/v2/partner/project-requests/{id}/quotes

GET   /api/v2/partner/quotes/{id}
PATCH /api/v2/partner/quotes/{id}

POST /api/v2/partner/quotes/{id}/send
POST /api/v2/partner/quotes/{id}/revise
POST /api/v2/partner/quotes/{id}/withdraw

```

Customer:

```http
GET /api/v2/project-requests/{id}/quotes
GET /api/v2/quotes/{id}

POST /api/v2/quotes/{id}/accept
POST /api/v2/quotes/{id}/decline

```

Sent versions are immutable.

---

# 29. Messaging schema

## conversations

```text
id
project_request_id
lead_connection_id
booking_id nullable
job_id nullable
status
created_at
updated_at

```

## conversation\_participants

```text
conversation_id
user_id
participant_type
provider_id nullable
joined_at
left_at nullable

```

## messages

```text
id
conversation_id
sender_user_id nullable
message_type
body_text nullable
metadata_json
created_at
edited_at nullable
deleted_at nullable

```

## message\_attachments

```text
id
message_id
storage_key
content_type
original_filename
size_bytes
checksum
scan_status

```

## message\_receipts

```text
message_id
user_id
delivered_at nullable
read_at nullable

```

Message types:

```text
TEXT
IMAGE
DOCUMENT
QUOTE
APPOINTMENT_PROPOSAL
SYSTEM

```

---

# 30. Messaging APIs

```http
GET /api/v2/conversations
GET /api/v2/conversations/{id}

GET /api/v2/conversations/{id}/messages

POST /api/v2/conversations/{id}/messages
POST /api/v2/conversations/{id}/attachments

POST /api/v2/conversations/{id}/read

```

Participant membership is mandatory server-side.

---

# 31. Booking bridge

Extend current Booking additively.

Recommended additions:

```text
project_request_id UUID NULL
accepted_quote_id UUID NULL
provider_id UUID NULL
worker_id UUID NULL

```

Existing historical Booking rows remain valid.

Do not destructive-backfill ambiguous historical rows.

Booking APIs:

```http
GET /api/v2/bookings/{id}
GET /api/v2/bookings/{id}/timeline

POST /api/v2/bookings/{id}/confirm
POST /api/v2/bookings/{id}/reschedule-request
POST /api/v2/bookings/{id}/cancel

```

When instant booking is false, requested timing is not confirmation.

---

# 32. Job schema

Reuse existing Job where possible.

Required execution states:

```text
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

Add/normalize:

```text
job_status_history
job_assignments
job_notes
job_evidence
job_additional_work

```

Never overwrite assignment history.

---

# 33. Job APIs

Customer/provider-safe:

```http
GET /api/v2/jobs/{id}
GET /api/v2/jobs/{id}/timeline

```

Provider/worker commands:

```http
POST /api/v2/jobs/{id}/en-route
POST /api/v2/jobs/{id}/arrive
POST /api/v2/jobs/{id}/start
POST /api/v2/jobs/{id}/complete

POST /api/v2/jobs/{id}/notes
POST /api/v2/jobs/{id}/evidence
POST /api/v2/jobs/{id}/additional-work

```

Ops:

```http
POST /api/v2/ops/jobs/{id}/assign
POST /api/v2/ops/jobs/{id}/reassign
POST /api/v2/ops/jobs/{id}/cancel

```

---

# 34. Review schema

## reviews

```text
id
job_id UNIQUE
customer_id
provider_id
overall_rating
body nullable
status
created_at
updated_at

```

## review\_dimensions

```text
review_id
dimension
rating

```

Dimensions:

```text
QUALITY
COMMUNICATION
TIMELINESS
VALUE

```

## review\_responses

```text
id
review_id
provider_id
body
created_at
updated_at

```

## review\_moderation

```text
id
review_id
moderator_id
action
reason
created_at

```

Only COMPLETED jobs are eligible.

---

# 35. Review APIs

Customer:

```http
POST /api/v2/jobs/{id}/review
GET  /api/v2/reviews/{id}

```

Provider:

```http
POST /api/v2/partner/reviews/{id}/response

```

Admin:

```http
POST /api/v2/admin/reviews/{id}/moderate

```

Public:

```http
GET /api/v2/providers/{slug}/reviews

```

---

# 36. Customer portal API inventory

Customer account:

```http
GET   /api/v2/customer/profile
PATCH /api/v2/customer/profile

GET /api/v2/customer/properties
POST /api/v2/customer/properties
GET /api/v2/customer/properties/{id}
PATCH /api/v2/customer/properties/{id}
DELETE /api/v2/customer/properties/{id}

GET /api/v2/customer/project-requests
GET /api/v2/customer/quotes
GET /api/v2/customer/conversations
GET /api/v2/customer/bookings
GET /api/v2/customer/jobs
GET /api/v2/customer/reviews

```

---

# 37. Provider portal complete API inventory

Dashboard:

```http
GET /api/v2/partner/dashboard

```

Profile:

```http
GET   /api/v2/partner/profile
PATCH /api/v2/partner/profile

```

Opportunities/leads:

```http
GET /api/v2/partner/opportunities
GET /api/v2/partner/opportunities/{id}
POST /api/v2/partner/opportunities/{id}/view
POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

GET /api/v2/partner/leads
GET /api/v2/partner/leads/{id}

```

Quotes:

```http
GET /api/v2/partner/quotes
GET /api/v2/partner/quotes/{id}
POST /api/v2/partner/project-requests/{id}/quotes
PATCH /api/v2/partner/quotes/{id}
POST /api/v2/partner/quotes/{id}/send
POST /api/v2/partner/quotes/{id}/revise
POST /api/v2/partner/quotes/{id}/withdraw

```

Jobs:

```http
GET /api/v2/partner/jobs
GET /api/v2/partner/jobs/{id}

```

Customers:

```http
GET /api/v2/partner/customers
GET /api/v2/partner/customers/{id}

```

Workers:

```http
GET /api/v2/partner/workers
POST /api/v2/partner/workers
GET /api/v2/partner/workers/{id}
PATCH /api/v2/partner/workers/{id}

```

Services:

```http
GET /api/v2/partner/services
PUT /api/v2/partner/services

```

Service areas:

```http
GET /api/v2/partner/service-areas
POST /api/v2/partner/service-areas
PATCH /api/v2/partner/service-areas/{id}
DELETE /api/v2/partner/service-areas/{id}

```

Availability:

```http
GET /api/v2/partner/availability
PUT /api/v2/partner/availability
POST /api/v2/partner/availability/exceptions
PATCH /api/v2/partner/availability/exceptions/{id}
DELETE /api/v2/partner/availability/exceptions/{id}

```

Credentials:

```http
GET /api/v2/partner/credentials
POST /api/v2/partner/credentials
GET /api/v2/partner/credentials/{id}
PATCH /api/v2/partner/credentials/{id}
POST /api/v2/partner/credentials/{id}/documents

```

Reviews:

```http
GET /api/v2/partner/reviews
POST /api/v2/partner/reviews/{id}/response

```

Analytics:

```http
GET /api/v2/partner/analytics/overview
GET /api/v2/partner/analytics/funnel
GET /api/v2/partner/analytics/jobs
GET /api/v2/partner/analytics/revenue

```

Billing later:

```http
GET /api/v2/partner/subscription
GET /api/v2/partner/billing

```

---

# 38. Worker portal APIs

```http
GET /api/v2/worker/profile

GET /api/v2/worker/jobs
GET /api/v2/worker/jobs/{id}

POST /api/v2/worker/jobs/{id}/en-route
POST /api/v2/worker/jobs/{id}/arrive
POST /api/v2/worker/jobs/{id}/start
POST /api/v2/worker/jobs/{id}/complete

POST /api/v2/worker/jobs/{id}/notes
POST /api/v2/worker/jobs/{id}/evidence

GET /api/v2/worker/availability
PUT /api/v2/worker/availability

GET /api/v2/worker/credentials

```

Worker access is restricted to its provider and eligible assignments.

---

# 39. Operations API inventory

Requests:

```http
GET /api/v2/ops/project-requests
GET /api/v2/ops/project-requests/{id}

POST /api/v2/ops/project-requests/{id}/qualify
POST /api/v2/ops/project-requests/{id}/mark-unserviceable

```

Matching:

```http
POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates

```

Opportunities:

```http
POST /api/v2/ops/project-requests/{id}/opportunities
POST /api/v2/ops/opportunities/{id}/withdraw

```

Jobs:

```http
GET /api/v2/ops/jobs
GET /api/v2/ops/jobs/{id}

POST /api/v2/ops/jobs/{id}/assign
POST /api/v2/ops/jobs/{id}/reassign
POST /api/v2/ops/jobs/{id}/cancel

```

Providers:

```http
GET /api/v2/ops/providers
GET /api/v2/ops/providers/{id}

```

Exceptions:

```http
GET /api/v2/ops/exceptions
GET /api/v2/ops/exceptions/{id}

POST /api/v2/ops/exceptions/{id}/acknowledge
POST /api/v2/ops/exceptions/{id}/resolve

```

Integrations:

```http
GET /api/v2/ops/integration-events
GET /api/v2/ops/integration-failures

POST /api/v2/ops/integration-events/{id}/retry
POST /api/v2/ops/integration-events/{id}/cancel

```

---

# 40. Admin API inventory

Users/RBAC:

```http
GET /api/v2/admin/users
GET /api/v2/admin/users/{id}

GET /api/v2/admin/roles
GET /api/v2/admin/permissions

PUT /api/v2/admin/users/{id}/roles

```

Providers:

```http
GET /api/v2/admin/providers
GET /api/v2/admin/providers/{id}

POST /api/v2/admin/providers/{id}/approve
POST /api/v2/admin/providers/{id}/suspend
POST /api/v2/admin/providers/{id}/reactivate

```

Credentials:

```http
GET /api/v2/admin/credentials
GET /api/v2/admin/credentials/{id}

POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke

```

Catalog:

```http
GET/POST/PATCH /api/v2/admin/catalog/...

```

Features:

```http
GET /api/v2/admin/features
GET /api/v2/admin/features/{key}
PUT /api/v2/admin/features/{key}

```

Audit:

```http
GET /api/v2/admin/audit-events
GET /api/v2/admin/audit-events/{id}

```

Reviews:

```http
GET /api/v2/admin/reviews
POST /api/v2/admin/reviews/{id}/moderate

```

---

# 41. RBAC

Canonical roles:

```text
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

```text
project_request.read
project_request.manage

matching.run
matching.inspect

opportunity.read
opportunity.respond
opportunity.manage

quote.read
quote.create
quote.send
quote.accept

conversation.read
conversation.send

booking.read
booking.manage

job.read
job.assign
job.execute
job.complete

provider.read
provider.manage
provider.credentials.manage
provider.credentials.verify
provider.suspend

review.create
review.respond
review.moderate

integration.read
integration.retry

finance.refund
finance.payout.approve

admin.users.manage
admin.features.manage
admin.audit.read

```

Permissions are enforced server-side.

Feature entitlement != permission.

---

# 42. Runtime capabilities API

Preserve PR-00 V1 endpoint and add V2 projection.

```http
GET /api/v2/capabilities

```

Eventually return:

```json
{
  "request_intake": true,
  "marketplace_matching": false,
  "provider_opportunities": false,
  "provider_self_service": false,
  "quotes": false,
  "messaging": false,
  "reviews": false,
  "instant_booking": false,
  "automatic_assignment": false,
  "payments": false,
  "payouts": false,
  "paid_leads": false,
  "marketing": false
}

```

Creating an endpoint does not enable the feature.

---

# 43. Audit schema

## audit\_events

```text
id
actor_id nullable
actor_type
tenant_id nullable
legal_entity_id nullable
action
resource_type
resource_id
correlation_id
ip_address nullable
user_agent nullable
metadata_json
created_at

```

Important actions:

```text
PROJECT_REQUEST_SUBMITTED
MATCHING_RUN_STARTED
OPPORTUNITY_SENT
OPPORTUNITY_ACCEPTED
QUOTE_SENT
QUOTE_ACCEPTED
BOOKING_CONFIRMED
JOB_ASSIGNED
JOB_COMPLETED
CREDENTIAL_VERIFIED
PROVIDER_SUSPENDED
INTEGRATION_RETRIED
REFUND_APPROVED
FEATURE_CHANGED

```

---

# 44. Transactional outbox schema

Extend current outbox toward:

```text
id UUID
event_type
aggregate_type
aggregate_id
aggregate_version
schema_version
payload JSONB

status

idempotency_key UNIQUE

attempt_count
max_attempts
available_at

lease_owner nullable
lease_until nullable

last_error_code nullable
last_error_message_redacted nullable
last_error_at nullable

correlation_id
causation_id nullable

created_at
delivered_at nullable

```

States:

```text
PENDING_CONFIGURATION
PENDING
PROCESSING
RETRYABLE
DELIVERED
FAILED_TERMINAL

```

Claim:

```sql
SELECT ...
FROM integration_events
WHERE status IN ('PENDING', 'RETRYABLE')
  AND available_at <= now()
  AND (lease_until IS NULL OR lease_until < now())
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT :batch_size;

```

---

# 45. Integration inbox

Add:

## integration\_inbox

```text
id
provider
external_event_id
event_type
schema_version nullable

request_hash
signature_verified
tenant_id nullable

status
payload JSONB

received_at
processing_started_at nullable
processed_at nullable

attempt_count
last_error_code nullable

```

Unique:

```text
(provider, external_event_id)

```

Sources:

```text
CODESTRA
ODOO
KLYROW
TELNEXA
N8N
STRIPE

```

---

# 46. Middleware architecture

Never:

```text
Browser → Odoo
Browser → Klyrow
Browser → Telnexa
Browser → n8n

```

Always:

```text
Browser
   ↓
BREERO API
   ↓
Domain transaction
   ↓
BREERO database + outbox
   ↓
COMMIT
   ↓
Worker
   ↓
Codestra/Kong
   ├── Odoo
   ├── Klyrow
   ├── Telnexa
   └── approved n8n workflow

```

Source-of-truth ownership:

```text
Breero DB = marketplace truth
Codestra   = integration/control plane
Odoo       = CRM projection
Klyrow     = email delivery
Telnexa    = SMS delivery
n8n        = approved orchestration
Stripe     = settlement authority only after activation

```

---

# 47. Form/event mapping

Customer ProjectRequest submission:

```text
project_request.submitted.v1

```

Provider application:

```text
provider_application.submitted.v1

```

Opportunity:

```text
opportunity.sent.v1
opportunity.accepted.v1
opportunity.declined.v1

```

Lead:

```text
lead.connected.v1

```

Quote:

```text
quote.sent.v1
quote.revised.v1
quote.accepted.v1
quote.declined.v1

```

Messaging:

```text
conversation.message_sent.v1

```

Booking:

```text
booking.created.v1
booking.confirmed.v1
booking.cancelled.v1

```

Job:

```text
job.assigned.v1
job.en_route.v1
job.arrived.v1
job.started.v1
job.completed.v1

```

Credential:

```text
credential.submitted.v1
credential.verified.v1
credential.expiring.v1
credential.expired.v1
credential.revoked.v1

```

Review:

```text
review.submitted.v1

```

Communications:

```text
communication.preference_changed.v1

```

---

# 48. Event envelope

Standard envelope:

```json
{
  "event_id": "uuid",
  "event_type": "project_request.submitted.v1",
  "schema_version": 1,
  "occurred_at": "ISO-8601",
  "aggregate_type": "project_request",
  "aggregate_id": "uuid",
  "aggregate_version": 3,
  "tenant_id": "uuid-or-null",
  "legal_entity_id": "uuid-or-null",
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "payload": {}
}

```

Never silently change event payloads.

---

# 49. Middleware adapter

Example abstraction:

```python
from typing import Protocol

class MiddlewareClient(Protocol):
    async def publish(
        self,
        event_type: str,
        payload: dict,
        *,
        idempotency_key: str,
        correlation_id: str,
    ) -> None: ...

```

Codestra implementation must use:

```text
TLS
machine credentials
correct audience
tenant authorization
idempotency key
correlation ID
bounded timeout
bounded retry
structured error mapping
redacted logs

```

---

# 50. Public/contact forms

Add durable entities rather than direct emails.

## contact\_requests

```text
id
name
email
phone nullable
subject
message
status
source_url
created_at

```

API:

```http
POST /api/v2/public/contact-requests

```

Outbox:

```text
contact_request.created.v1

```

Support/admin API:

```http
GET /api/v2/ops/contact-requests
GET /api/v2/ops/contact-requests/{id}
POST /api/v2/ops/contact-requests/{id}/resolve

```

---

# 51. Communication preferences

Preserve compliance domain.

API should include:

```http
GET /api/v2/customer/communication-preferences
PUT /api/v2/customer/communication-preferences

POST /api/v2/public/communication-preferences

```

Track:

```text
transactional email
transactional SMS
marketing email
marketing SMS
purpose
channel
disclosure
policy version
source
timestamp

```

Explicit re-opt-in only clears matching channel/purpose suppression.

---

# 52. Analytics backend

## analytics\_events

Consider append-only product events or send to analytics sink from outbox.

Capture:

```text
request_started
request_submitted
request_qualified
request_matched

opportunity_sent
opportunity_viewed
opportunity_accepted

quote_created
quote_sent
quote_accepted

booking_created

job_started
job_completed

review_submitted
repeat_request

```

Provider endpoints:

```http
GET /api/v2/partner/analytics/overview
GET /api/v2/partner/analytics/funnel
GET /api/v2/partner/analytics/jobs
GET /api/v2/partner/analytics/revenue

```

Ops:

```http
GET /api/v2/ops/analytics/funnel
GET /api/v2/ops/analytics/matching
GET /api/v2/ops/analytics/providers
GET /api/v2/ops/analytics/jobs

```

---

# 53. Payment phase — disabled until authorized

Later tables:

```text
payment_intents
payments
payment_events
refunds
platform_fees
provider_balances
payouts

```

Later APIs:

```http
POST /api/v2/payments/intents
GET  /api/v2/payments/{id}

POST /api/v2/admin/refunds
GET  /api/v2/partner/payouts

```

Rules:

```text
Stripe webhook authoritative
redirect is not settlement authority
idempotent webhook processing
customer charge != provider payout
refund audited
payout finance-controlled

```

Until approved:

```text
payments=false
payouts=false

```

---

# 54. Provider subscriptions — later

Tables:

```text
subscription_plans
provider_subscriptions
subscription_entitlements
subscription_events

```

Plans can eventually support:

```text
FREE
PRO
BUSINESS

```

Do not mix entitlements with RBAC.

---

# 55. Required Alembic sequence

Use actual current head, not hard-coded revision numbers.

Recommended conceptual order:

```text
ProjectRequest
Catalog questionnaire additions
Provider marketplace extensions
Provider onboarding
Credentials/trust additions
Availability
Matching
Opportunities
Quotes
Conversations
Booking bridge
Reviews
Integration inbox/outbox
Analytics
Transactions
Subscriptions

```

Migration rules:

```text
additive first
bounded backfill
validate
then add strict constraints
no production DB in tests
practical downgrade where safe
no destructive historical rewrite

```

---

# 56. Backend testing required for every branch

Run:

```text
Ruff
compileall
pytest

PostgreSQL/PostGIS integration suite

Alembic upgrade
schema-drift validation
prior-head → new-head upgrade
practical downgrade where possible

domain transition tests
repository tests

authorization tests
negative authorization tests

idempotency tests
concurrency tests

outbox/inbox tests where applicable

OpenAPI generation
contract compatibility

```

---

# 57. Mandatory negative-security tests

Prove:

```text
Provider A cannot read Provider B opportunity
Provider A cannot read Provider B lead
Provider A cannot read Provider B quote
Provider A cannot read Provider B conversation
Provider A cannot read Provider B customer PII
Provider A cannot read Provider B job

Customer A cannot read Customer B request
Customer A cannot read Customer B quote
Customer A cannot read Customer B conversation

Worker cannot execute unassigned provider job

Expired credential cannot match
Revoked credential cannot match
Suspended provider cannot match

Dispatcher cannot approve payout
Support cannot verify credentials
Unmatched provider cannot obtain customer contact data

```

---

# 58. Reliability acceptance tests

Prove:

```text
duplicate request submit
→ one logical submission

duplicate opportunity acceptance
→ one LeadConnection

duplicate quote acceptance
→ one acceptance

duplicate booking command
→ one Booking

duplicate webhook
→ one business effect

worker crash
→ lease expires
→ event safely reclaimed

middleware disabled
→ PENDING_CONFIGURATION

middleware enabled
→ PENDING
→ delivered once

retryable failure
→ retried

terminal failure
→ visible to Ops

expired hold
→ no capacity consumption

```

---

# 59. Backend Marketplace MVP definition

Backend is MVP-ready only when:

```text
ProjectRequest
→ qualification
→ matching
→ 3 eligible candidates
→ opportunities
→ provider acceptance
→ LeadConnection
→ conversation
→ versioned quote
→ customer acceptance
→ scheduling
→ Booking
→ eligible worker
→ Job completion
→ verified review

```

works with payments disabled.

Also prove:

```text
zero-provider path
expired-credential path
suspended-provider path
integration outage
duplicate command
duplicate event
worker lease recovery
cross-tenant isolation
payments disabled

```

---

# 60. Backend completion output for every PR

Every PR description must include:

```text
BASE_SHA
FINAL_SHA
ALEMBIC_PREVIOUS_HEAD
ALEMBIC_NEW_HEAD
MIGRATION_UPGRADE
MIGRATION_DOWNGRADE
POSTGRES_TESTS
UNIT_TESTS
AUTH_TESTS
IDEMPOTENCY_TESTS
CONCURRENCY_TESTS
OPENAPI
OUTBOX_INBOX_TESTS
FEATURE_FLAGS_ENABLED
PRODUCTION_DB_TOUCHED
KNOWN_RISKS
ROLLBACK

```

Do not enable a production capability simply because its code exists.
