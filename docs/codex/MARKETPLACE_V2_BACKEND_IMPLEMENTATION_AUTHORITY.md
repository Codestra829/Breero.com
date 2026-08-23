# BREERO Marketplace V2 — Backend, Database, API and Middleware Production Specification

## Status and safety boundary

This document replaces the earlier backend-authority draft and is documentation-only implementation authority for `appolon1908-hue/Breero.com`. It must not be deployed. Complete and human-merge PR-00 release safety and the Marketplace V2 planning authority before creating implementation branches from the latest merged target.

The current request-only/manual-dispatch behavior remains authoritative. Payments, payouts, paid leads, provider self-service, marketplace matching, messaging, reviews, instant booking, automatic assignment, automatic confirmation, marketing, unrestricted email/SMS and external automation remain disabled until separately implemented, tested and authorized.

The canonical Keycloak issuer is `https://auth.codestra.co/realms/codestra`. `auth.codestra.agency` is deprecated and must not be used in new configuration.
## 1. Scope

This document is the implementation authority for the BREERO backend.

Backend owns:

- FastAPI
- PostgreSQL
- PostGIS
- Alembic
- SQLAlchemy
- authentication integration
- authorization
- RBAC
- customer data
- provider data
- service catalog
- ProjectRequest
- matching
- opportunities
- leads
- quotes
- messaging persistence
- availability
- scheduling
- bookings
- jobs
- reviews
- credentials
- trust and safety
- operations
- administration
- payments when activated
- provider payouts when activated
- subscriptions when activated
- audit
- analytics events
- transactional outbox
- integration inbox
- Codestra middleware integration
- Odoo projection
- Klyrow email events
- Telnexa SMS events
- n8n approved workflow events
- observability
- OpenAPI
- backend testing

Frontend code must not be implemented in backend PRs.

---

# 2. Backend Git branches

Implement sequentially.

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
be/marketplace-v2-payments
be/marketplace-v2-subscriptions

```

One PR per branch.

Do not create another mega-PR.

---

# 3. Core architecture

Use the existing BREERO application architecture:

```text
FastAPI Router
      ↓
Domain Service / Command
      ↓
Repository / Query
      ↓
Async SQLAlchemy
      ↓
PostgreSQL/PostGIS

```

PostgreSQL is authoritative.

Redis is not authoritative.

Redis may contain:

```text
rate limits
cache
availability cache
matching cache
short-lived distributed locks
background queue state

```

Redis must never be the only storage for:

```text
ProjectRequest
Opportunity
LeadConnection
Quote
Conversation
Booking
Job
Credential
Review
Payment
Payout

```

---

# 4. Canonical marketplace lifecycle

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
Booking
      ↓
Job
      ↓
Verified Review

```

Definitions:

```text
ProjectRequest = demand
Matching       = eligibility and ranking
Opportunity    = provider invitation
LeadConnection = authorized provider/customer connection
Quote          = provider commercial offer
Booking        = scheduling result
Job            = execution
Review         = completed-job trust signal

```

Booking must not own:

- demand qualification
- provider search
- provider ranking
- lead generation
- quoting
- messaging

---

# 5. API versioning

Keep `/api/v1` operational while V2 is introduced.

New marketplace contract:

```text
/api/v2

```

Do not remove V1 routes until consumers have migrated.

Mount:

```text
/api/v2/public
/api/v2/catalog
/api/v2/project-requests
/api/v2/providers
/api/v2/customer
/api/v2/partner
/api/v2/worker
/api/v2/quotes
/api/v2/conversations
/api/v2/bookings
/api/v2/jobs
/api/v2/reviews
/api/v2/ops
/api/v2/admin
/api/v2/integrations

```

---

# 6. Production database standards

All primary identifiers:

```text
UUID

```

All timestamps:

```text
TIMESTAMPTZ

```

Money:

```text
BIGINT minor units

```

Example:

```text
$12.50 = 1250

```

Never store currency values as float.

Currency:

```text
CHAR(3)

```

Examples:

```text
USD
CAD
EUR

```

Use:

```text
created_at
updated_at

```

on mutable entities.

Important aggregates also use:

```text
version INTEGER NOT NULL

```

for optimistic concurrency.

Prefer CHECK constraints or application-owned status validation over hard-to-migrate PostgreSQL ENUMs unless the repository has already standardized on database ENUMs.

---

# 7. Customer schema

## customer\_profiles

```text
id UUID PK
user_id UUID UNIQUE NOT NULL

first_name VARCHAR
last_name VARCHAR
display_name VARCHAR NULL

primary_email VARCHAR
primary_phone VARCHAR NULL

timezone VARCHAR

created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ

```

Indexes:

```text
UNIQUE(user_id)
INDEX(primary_email)

```

---

# 8. Customer properties

## customer\_properties

```text
id UUID PK
customer_id UUID FK NOT NULL

name VARCHAR
property_type VARCHAR

year_built INTEGER NULL
square_feet INTEGER NULL
bedrooms NUMERIC NULL
bathrooms NUMERIC NULL

active BOOLEAN

created_at
updated_at

```

Index:

```text
(customer_id, active)

```

---

# 9. Addresses

Preserve and extend existing address model.

Required:

```text
id UUID PK

customer_id UUID NULL
property_id UUID NULL

line1
line2 NULL
city
region
postal_code
country_code

latitude DOUBLE PRECISION
longitude DOUBLE PRECISION

location GEOGRAPHY(Point,4326)

timezone_name
geocode_status

created_at
updated_at

```

PostGIS:

```sql
CREATE INDEX addresses_location_gist
ON addresses
USING GIST(location);

```

---

# 10. Service catalog schema

## service\_categories

```text
id UUID PK
slug VARCHAR UNIQUE
name VARCHAR
description TEXT
sort_order INTEGER
active BOOLEAN

```

## services

Extend existing services.

```text
id UUID PK
category_id UUID FK

slug VARCHAR UNIQUE
name VARCHAR
description TEXT

active BOOLEAN
is_bookable BOOLEAN

default_fulfillment_mode VARCHAR
requires_provider_quote BOOLEAN

minimum_notice_minutes INTEGER

created_at
updated_at

```

Fulfillment modes:

```text
INSTANT_BOOK
QUOTE_REQUIRED
MANUAL_DISPATCH
UNSERVICEABLE

```

---

# 11. Dynamic service questionnaire

## service\_questions

```text
id UUID PK
service_id UUID FK

key VARCHAR
label VARCHAR
help_text TEXT NULL

question_type VARCHAR
required BOOLEAN

sort_order INTEGER
active BOOLEAN

validation_json JSONB

created_at
updated_at

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

Unique:

```text
(service_id, key)

```

## service\_question\_options

```text
id UUID PK
question_id UUID FK

value VARCHAR
label VARCHAR

sort_order INTEGER
active BOOLEAN

```

## service\_question\_rules

```text
id UUID PK

service_id UUID
source_question_id UUID
operator VARCHAR
expected_value_json JSONB

target_question_id UUID
action VARCHAR

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

Public:

```http
GET /api/v2/catalog/categories
GET /api/v2/catalog/categories/{slug}

GET /api/v2/catalog/services
GET /api/v2/catalog/services/{slug}
GET /api/v2/catalog/services/{id}/questions

```

Admin:

```http
POST  /api/v2/admin/catalog/categories
PATCH /api/v2/admin/catalog/categories/{id}

POST  /api/v2/admin/catalog/services
PATCH /api/v2/admin/catalog/services/{id}

POST   /api/v2/admin/catalog/services/{id}/questions
PATCH  /api/v2/admin/catalog/questions/{id}
DELETE /api/v2/admin/catalog/questions/{id}

```

---

# 13. ProjectRequest schema

## project\_requests

```text
id UUID PK

reference VARCHAR UNIQUE

customer_id UUID NULL
property_id UUID NULL
service_id UUID NOT NULL
address_id UUID NOT NULL
legal_entity_id UUID NULL

status VARCHAR NOT NULL
fulfillment_mode VARCHAR NULL

title VARCHAR NULL
description TEXT NOT NULL

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

Indexes:

```text
(customer_id, created_at DESC)
(status, created_at)
(service_id, status)
(address_id)

```

---

# 14. Project answers

## project\_request\_answers

```text
id UUID PK
project_request_id UUID FK
question_id UUID FK

answer_json JSONB

created_at
updated_at

```

Unique:

```text
(project_request_id, question_id)

```

---

# 15. Project attachments

## project\_request\_attachments

```text
id UUID PK
project_request_id UUID FK

storage_key VARCHAR
original_filename VARCHAR
content_type VARCHAR
size_bytes BIGINT
checksum_sha256 VARCHAR

scan_status VARCHAR

created_by UUID NULL
created_at

```

Scan states:

```text
PENDING
CLEAN
REJECTED
FAILED

```

Never store uploaded binary content directly in PostgreSQL.

---

# 16. Project request history

## project\_request\_status\_history

```text
id UUID PK
project_request_id UUID FK

from_status VARCHAR NULL
to_status VARCHAR

reason_code VARCHAR NULL
actor_id UUID NULL

metadata_json JSONB

created_at

```

History is append-only.

---

# 17. ProjectRequest APIs

Customer:

```http
POST   /api/v2/project-requests
GET    /api/v2/project-requests/{id}
PATCH  /api/v2/project-requests/{id}

PUT    /api/v2/project-requests/{id}/answers/{questionId}
DELETE /api/v2/project-requests/{id}/answers/{questionId}

POST   /api/v2/project-requests/{id}/attachments
DELETE /api/v2/project-requests/{id}/attachments/{attachmentId}

POST /api/v2/project-requests/{id}/submit
POST /api/v2/project-requests/{id}/cancel

GET /api/v2/project-requests/{id}/matches
GET /api/v2/project-requests/{id}/quotes

```

Customer portal:

```http
GET /api/v2/customer/project-requests

```

Operations:

```http
GET /api/v2/ops/project-requests
GET /api/v2/ops/project-requests/{id}

POST /api/v2/ops/project-requests/{id}/qualify
POST /api/v2/ops/project-requests/{id}/mark-unserviceable

```

---

# 18. Provider organization schema

## provider\_organizations

```text
id UUID PK

legal_name VARCHAR
display_name VARCHAR
slug VARCHAR UNIQUE

entity_type VARCHAR

status VARCHAR

website VARCHAR NULL
primary_email VARCHAR
primary_phone VARCHAR

timezone VARCHAR

created_at
updated_at

```

Statuses:

```text
DRAFT
PENDING_REVIEW
ACTIVE
SUSPENDED
REJECTED
CLOSED

```

---

# 19. Provider profile

## provider\_profiles

```text
provider_id UUID PK/FK

headline VARCHAR NULL
description TEXT

years_in_business INTEGER NULL

logo_storage_key VARCHAR NULL
cover_storage_key VARCHAR NULL

response_time_minutes INTEGER NULL

verified_jobs_count INTEGER DEFAULT 0

rating_average NUMERIC(3,2)
rating_count INTEGER

public_profile_enabled BOOLEAN

created_at
updated_at

```

---

# 20. Provider members

## provider\_members

```text
id UUID PK
provider_id UUID FK
user_id UUID FK

role VARCHAR
status VARCHAR

created_at
updated_at

```

Unique:

```text
(provider_id, user_id)

```

---

# 21. Provider workers

## provider\_workers

```text
id UUID PK

provider_id UUID FK
user_id UUID NULL

first_name
last_name

email
phone

status VARCHAR

hire_date DATE NULL

created_at
updated_at

```

States:

```text
INVITED
ACTIVE
INACTIVE
SUSPENDED

```

---

# 22. Provider services

## provider\_services

```text
provider_id UUID FK
service_id UUID FK

active BOOLEAN

starting_price_minor BIGINT NULL
currency CHAR(3)

created_at
updated_at

```

PK/unique:

```text
(provider_id, service_id)

```

---

# 23. Provider service areas

## provider\_service\_areas

```text
id UUID PK

provider_id UUID FK
service_id UUID NULL

area_type VARCHAR

area GEOGRAPHY NULL

center GEOGRAPHY(Point,4326) NULL
radius_meters INTEGER NULL

active BOOLEAN

created_at
updated_at

```

Types:

```text
POLYGON
RADIUS

```

Indexes:

```sql
CREATE INDEX provider_service_areas_area_gist
ON provider_service_areas
USING GIST(area);

CREATE INDEX provider_service_areas_center_gist
ON provider_service_areas
USING GIST(center);

```

---

# 24. Provider gallery

## provider\_gallery

```text
id UUID PK
provider_id UUID FK

storage_key
caption NULL
sort_order
active

created_at

```

---

# 25. Provider APIs

Public:

```http
GET /api/v2/providers

GET /api/v2/providers/{slug}

GET /api/v2/providers/{slug}/services
GET /api/v2/providers/{slug}/reviews
GET /api/v2/providers/{slug}/service-area
GET /api/v2/providers/{slug}/availability-summary

```

Partner:

```http
GET   /api/v2/partner/profile
PATCH /api/v2/partner/profile

GET /api/v2/partner/services
PUT /api/v2/partner/services

GET    /api/v2/partner/service-areas
POST   /api/v2/partner/service-areas
PATCH  /api/v2/partner/service-areas/{id}
DELETE /api/v2/partner/service-areas/{id}

GET    /api/v2/partner/workers
POST   /api/v2/partner/workers
GET    /api/v2/partner/workers/{id}
PATCH  /api/v2/partner/workers/{id}

POST /api/v2/partner/workers/{id}/activate
POST /api/v2/partner/workers/{id}/deactivate

```

---

# 26. Provider application schema

## provider\_applications

```text
id UUID PK

user_id UUID NULL

legal_name
display_name

contact_first_name
contact_last_name

email
phone
website NULL

status VARCHAR

submission_json JSONB

submitted_at NULL
reviewed_at NULL
reviewed_by NULL

version INTEGER

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
id UUID PK
application_id UUID FK

from_status
to_status

reason TEXT NULL
actor_id UUID NULL

created_at

```

---

# 27. Provider onboarding APIs

Public:

```http
POST /api/v2/public/provider-applications

```

Provider:

```http
GET   /api/v2/partner/onboarding
PATCH /api/v2/partner/onboarding
POST  /api/v2/partner/onboarding/submit

```

Admin:

```http
GET /api/v2/admin/provider-applications
GET /api/v2/admin/provider-applications/{id}

POST /api/v2/admin/provider-applications/{id}/request-information
POST /api/v2/admin/provider-applications/{id}/approve
POST /api/v2/admin/provider-applications/{id}/reject

```

---

# 28. Credential requirement schema

## credential\_requirements

```text
id UUID PK

service_id UUID NULL

jurisdiction VARCHAR
credential_type VARCHAR
subject_type VARCHAR

required BOOLEAN
verification_mode VARCHAR

active BOOLEAN

created_at
updated_at

```

Subject:

```text
PROVIDER
WORKER

```

---

# 29. Provider credentials

## provider\_credentials

```text
id UUID PK

provider_id UUID FK
worker_id UUID NULL

credential_type VARCHAR

credential_number_ciphertext BYTEA NULL
credential_number_last4 VARCHAR NULL

issuing_authority VARCHAR
jurisdiction VARCHAR

effective_at DATE NULL
expires_at DATE NULL

status VARCHAR

document_id UUID NULL

created_at
updated_at

```

Statuses:

```text
PENDING
VERIFIED
REJECTED
EXPIRED
REVOKED

```

Sensitive credential numbers must be encrypted.

---

# 30. Credential verification

## credential\_verifications

```text
id UUID PK

credential_id UUID FK

status VARCHAR

verification_source VARCHAR
reviewer_id UUID NULL

reason_code VARCHAR NULL
metadata_json JSONB

verified_at TIMESTAMPTZ

created_at

```

---

# 31. Provider documents

## provider\_documents

```text
id UUID PK

provider_id UUID FK
worker_id UUID NULL

document_type VARCHAR

storage_key VARCHAR
content_type VARCHAR
checksum_sha256 VARCHAR

scan_status VARCHAR

created_at

```

---

# 32. Credential APIs

Provider:

```http
GET  /api/v2/partner/credentials
POST /api/v2/partner/credentials

GET   /api/v2/partner/credentials/{id}
PATCH /api/v2/partner/credentials/{id}

POST   /api/v2/partner/credentials/{id}/documents
DELETE /api/v2/partner/credentials/{id}/documents/{documentId}

```

Admin/trust:

```http
GET /api/v2/admin/credentials
GET /api/v2/admin/credentials/{id}

POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke

```

---

# 33. Availability schema

## provider\_availability\_rules

```text
id UUID PK

provider_id UUID FK
worker_id UUID NULL

weekday SMALLINT

start_time TIME
end_time TIME

capacity INTEGER

timezone VARCHAR

effective_from DATE
effective_until DATE NULL

active BOOLEAN

created_at
updated_at

```

Constraint:

```text
weekday 0–6
end_time > start_time
capacity >= 0

```

---

# 34. Availability exceptions

## provider\_availability\_exceptions

```text
id UUID PK

provider_id UUID FK
worker_id UUID NULL

date DATE

start_time TIME NULL
end_time TIME NULL

capacity_override INTEGER NULL
unavailable BOOLEAN

reason VARCHAR NULL

created_at
updated_at

```

---

# 35. Availability APIs

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

Public/customer:

```http
GET /api/v2/providers/{slug}/availability-summary
GET /api/v2/project-requests/{id}/availability

```

---

# 36. Matching run schema

## matching\_runs

```text
id UUID PK

project_request_id UUID FK

algorithm VARCHAR
algorithm_version VARCHAR

configuration_json JSONB

status VARCHAR

started_at
completed_at NULL

created_by UUID NULL

created_at

```

---

# 37. Matching candidates

## match\_candidates

```text
id UUID PK

matching_run_id UUID FK
provider_id UUID FK

eligible BOOLEAN

rank INTEGER NULL
score NUMERIC NULL

distance_meters INTEGER NULL

availability_score NUMERIC NULL
distance_score NUMERIC NULL
rating_score NUMERIC NULL
completion_score NUMERIC NULL
acceptance_score NUMERIC NULL
response_score NUMERIC NULL
price_score NUMERIC NULL
relationship_score NUMERIC NULL
quality_score NUMERIC NULL

created_at

```

Unique:

```text
(matching_run_id, provider_id)

```

---

# 38. Matching reasons

## match\_reasons

```text
id UUID PK

candidate_id UUID FK

reason_type VARCHAR
reason_code VARCHAR

passed BOOLEAN

score_delta NUMERIC NULL

detail_json JSONB

created_at

```

---

# 39. Matching eligibility

Hard gates:

```text
provider is ACTIVE
provider supports service
request location is in service area
all mandatory credentials valid
insurance valid when required
provider not suspended
qualified worker available
schedule available
capacity available
legal entity compatible

```

If one mandatory gate fails:

```text
eligible = false

```

---

# 40. Matching V1 scoring

```text
Availability                 20
Distance/service area        20
Verified rating              15
Completion rate              10
Opportunity acceptance       10
Response speed               10
Price competitiveness         5
Prior relationship            5
BREERO quality score          5

```

Do not use ML for V1.

---

# 41. Matching APIs

Ops:

```http
POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates
GET /api/v2/ops/matching-runs/{id}/candidates/{candidateId}

```

Customer-safe:

```http
GET /api/v2/project-requests/{id}/matches

```

---

# 42. Opportunity schema

## opportunities

```text
id UUID PK

project_request_id UUID FK
provider_id UUID FK

matching_run_id UUID FK
candidate_id UUID FK

status VARCHAR

sent_at TIMESTAMPTZ
viewed_at TIMESTAMPTZ NULL
responded_at TIMESTAMPTZ NULL
expires_at TIMESTAMPTZ

version INTEGER

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

---

# 43. Opportunity history

## opportunity\_status\_history

```text
id UUID PK

opportunity_id UUID FK

from_status
to_status

reason NULL

actor_id UUID NULL

created_at

```

---

# 44. Lead connections

## lead\_connections

```text
id UUID PK

project_request_id UUID FK
provider_id UUID FK
opportunity_id UUID FK

status VARCHAR

customer_contact_access_level VARCHAR

connected_at TIMESTAMPTZ
closed_at TIMESTAMPTZ NULL

created_at
updated_at

```

Contact access:

```text
NONE
MASKED
AUTHORIZED

```

---

# 45. Opportunity APIs

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

---

# 46. Quote schema

## quotes

```text
id UUID PK

project_request_id UUID FK
lead_connection_id UUID FK

provider_id UUID FK

current_version_id UUID NULL

status VARCHAR

currency CHAR(3)

version INTEGER

created_at
updated_at

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

# 47. Quote versions

## quote\_versions

```text
id UUID PK

quote_id UUID FK

version_number INTEGER

subtotal_minor BIGINT
tax_minor BIGINT
discount_minor BIGINT
fee_minor BIGINT
total_minor BIGINT

notes TEXT NULL

valid_until TIMESTAMPTZ

created_by UUID

created_at
sent_at NULL

```

Unique:

```text
(quote_id, version_number)

```

Sent versions are immutable.

---

# 48. Quote line items

## quote\_line\_items

```text
id UUID PK

quote_version_id UUID FK

type VARCHAR
description VARCHAR

quantity NUMERIC

unit_price_minor BIGINT
amount_minor BIGINT

sort_order INTEGER

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

---

# 49. Quote history

## quote\_status\_history

```text
id UUID PK

quote_id UUID FK

from_status
to_status

quote_version_id UUID

actor_id UUID

created_at

```

---

# 50. Quote APIs

Provider:

```http
GET /api/v2/partner/quotes
GET /api/v2/partner/quotes/{id}

POST /api/v2/partner/project-requests/{id}/quotes
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

Acceptance must be idempotent.

---

# 51. Conversation schema

## conversations

```text
id UUID PK

project_request_id UUID FK
lead_connection_id UUID FK

booking_id UUID NULL
job_id UUID NULL

status VARCHAR

created_at
updated_at

```

---

# 52. Conversation participants

## conversation\_participants

```text
conversation_id UUID FK
user_id UUID FK

participant_type VARCHAR

provider_id UUID NULL

joined_at
left_at NULL

```

Unique:

```text
(conversation_id, user_id)

```

---

# 53. Messages

## messages

```text
id UUID PK

conversation_id UUID FK

sender_user_id UUID NULL

message_type VARCHAR

body_text TEXT NULL
metadata_json JSONB

created_at
edited_at NULL
deleted_at NULL

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

# 54. Message attachments

## message\_attachments

```text
id UUID PK
message_id UUID FK

storage_key
content_type
original_filename
size_bytes
checksum_sha256

scan_status

created_at

```

---

# 55. Message receipts

## message\_receipts

```text
message_id UUID FK
user_id UUID FK

delivered_at NULL
read_at NULL

```

Unique:

```text
(message_id, user_id)

```

---

# 56. Messaging APIs

```http
GET /api/v2/conversations
GET /api/v2/conversations/{id}

GET /api/v2/conversations/{id}/messages

POST /api/v2/conversations/{id}/messages
POST /api/v2/conversations/{id}/attachments

POST /api/v2/conversations/{id}/read

```

Server must validate conversation membership.

---

# 57. Booking bridge

Extend existing Booking rather than replace historical records.

Add nullable:

```text
project_request_id UUID
accepted_quote_id UUID
provider_id UUID
worker_id UUID

```

Do not force legacy rows to populate these fields.

---

# 58. Booking APIs

```http
GET /api/v2/bookings/{id}
GET /api/v2/bookings/{id}/timeline

POST /api/v2/bookings/{id}/confirm
POST /api/v2/bookings/{id}/reschedule-request
POST /api/v2/bookings/{id}/cancel

```

If:

```text
instant_booking = false

```

preferred time remains a request until backend confirmation.

---

# 59. Job domain

Preserve current Job where possible.

Execution states:

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

---

# 60. Job assignment history

## job\_assignments

```text
id UUID PK

job_id UUID FK
provider_id UUID FK
worker_id UUID NULL

assigned_at
unassigned_at NULL

assigned_by UUID

reason VARCHAR NULL

```

Never overwrite old assignment.

---

# 61. Job APIs

Customer/provider:

```http
GET /api/v2/jobs/{id}
GET /api/v2/jobs/{id}/timeline

```

Provider/worker:

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

# 62. Reviews

## reviews

```text
id UUID PK

job_id UUID UNIQUE FK
customer_id UUID FK
provider_id UUID FK

overall_rating SMALLINT

body TEXT NULL

status VARCHAR

created_at
updated_at

```

Constraint:

```text
overall_rating BETWEEN 1 AND 5

```

---

# 63. Review dimensions

## review\_dimensions

```text
review_id UUID FK

dimension VARCHAR
rating SMALLINT

```

Dimensions:

```text
QUALITY
COMMUNICATION
TIMELINESS
VALUE

```

Unique:

```text
(review_id, dimension)

```

---

# 64. Review responses

## review\_responses

```text
id UUID PK

review_id UUID FK
provider_id UUID FK

body TEXT

created_at
updated_at

```

---

# 65. Review moderation

## review\_moderation

```text
id UUID PK

review_id UUID FK
moderator_id UUID

action VARCHAR
reason TEXT

created_at

```

---

# 66. Review APIs

Customer:

```http
POST /api/v2/jobs/{id}/review
GET /api/v2/reviews/{id}

```

Provider:

```http
GET /api/v2/partner/reviews
POST /api/v2/partner/reviews/{id}/response

```

Public:

```http
GET /api/v2/providers/{slug}/reviews

```

Admin:

```http
GET /api/v2/admin/reviews
POST /api/v2/admin/reviews/{id}/moderate

```

Only completed jobs are eligible.

---

# 67. Customer portal API inventory

```http
GET   /api/v2/customer/profile
PATCH /api/v2/customer/profile

GET  /api/v2/customer/properties
POST /api/v2/customer/properties

GET    /api/v2/customer/properties/{id}
PATCH  /api/v2/customer/properties/{id}
DELETE /api/v2/customer/properties/{id}

GET /api/v2/customer/project-requests
GET /api/v2/customer/quotes
GET /api/v2/customer/conversations
GET /api/v2/customer/bookings
GET /api/v2/customer/jobs
GET /api/v2/customer/reviews

GET /api/v2/customer/communication-preferences
PUT /api/v2/customer/communication-preferences

```

---

# 68. Provider portal API inventory

Dashboard:

```http
GET /api/v2/partner/dashboard

```

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

Areas:

```http
GET    /api/v2/partner/service-areas
POST   /api/v2/partner/service-areas
PATCH  /api/v2/partner/service-areas/{id}
DELETE /api/v2/partner/service-areas/{id}

```

Workers:

```http
GET /api/v2/partner/workers
POST /api/v2/partner/workers
GET /api/v2/partner/workers/{id}
PATCH /api/v2/partner/workers/{id}

```

Availability:

```http
GET /api/v2/partner/availability
PUT /api/v2/partner/availability

POST   /api/v2/partner/availability/exceptions
PATCH  /api/v2/partner/availability/exceptions/{id}
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

Opportunities:

```http
GET /api/v2/partner/opportunities
GET /api/v2/partner/opportunities/{id}

POST /api/v2/partner/opportunities/{id}/view
POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

```

Leads:

```http
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

---

# 69. Worker APIs

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

---

# 70. Ops APIs

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

Analytics:

```http
GET /api/v2/ops/analytics/funnel
GET /api/v2/ops/analytics/matching
GET /api/v2/ops/analytics/providers
GET /api/v2/ops/analytics/jobs

```

---

# 71. Admin APIs

Users:

```http
GET /api/v2/admin/users
GET /api/v2/admin/users/{id}

```

Roles:

```http
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

Applications:

```http
GET /api/v2/admin/provider-applications
GET /api/v2/admin/provider-applications/{id}

POST /api/v2/admin/provider-applications/{id}/approve
POST /api/v2/admin/provider-applications/{id}/reject
POST /api/v2/admin/provider-applications/{id}/request-information

```

Credentials:

```http
GET /api/v2/admin/credentials
GET /api/v2/admin/credentials/{id}

POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke

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

# 72. Public APIs

Capabilities:

```http
GET /api/v2/capabilities

```

Contact:

```http
POST /api/v2/public/contact-requests

```

Provider application:

```http
POST /api/v2/public/provider-applications

```

Communication preferences:

```http
POST /api/v2/public/communication-preferences

```

Catalog/provider discovery uses the public catalog/provider routes.

---

# 73. Contact request schema

## contact\_requests

```text
id UUID PK

name
email
phone NULL

subject
message

status VARCHAR

source_url NULL

created_at
updated_at

```

States:

```text
NEW
IN_PROGRESS
RESOLVED
CLOSED

```

---

# 74. Contact APIs

Public:

```http
POST /api/v2/public/contact-requests

```

Ops:

```http
GET /api/v2/ops/contact-requests
GET /api/v2/ops/contact-requests/{id}

POST /api/v2/ops/contact-requests/{id}/resolve

```

---

# 75. RBAC

Roles:

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

Backend authorization is authoritative.

---

# 76. Audit events

## audit\_events

```text
id UUID PK

actor_id UUID NULL
actor_type VARCHAR

tenant_id UUID NULL
legal_entity_id UUID NULL

action VARCHAR

resource_type VARCHAR
resource_id UUID NULL

correlation_id VARCHAR

ip_address INET NULL
user_agent TEXT NULL

metadata_json JSONB

created_at

```

Index:

```text
(resource_type, resource_id, created_at)
(actor_id, created_at)
(correlation_id)

```

---

# 77. Idempotency

Add or standardize:

## idempotency\_records

```text
id UUID PK

actor_key VARCHAR
operation VARCHAR
idempotency_key VARCHAR

request_hash VARCHAR

status VARCHAR

response_code INTEGER NULL
response_json JSONB NULL

resource_type VARCHAR NULL
resource_id UUID NULL

expires_at TIMESTAMPTZ

created_at
updated_at

```

Unique:

```text
(actor_key, operation, idempotency_key)

```

A reused key with a different request hash returns:

```text
409 IDEMPOTENCY_KEY_REUSED

```

---

# 78. Transactional outbox

Use:

## integration\_events

```text
id UUID PK

event_type VARCHAR

aggregate_type VARCHAR
aggregate_id UUID
aggregate_version INTEGER

schema_version INTEGER

payload JSONB

status VARCHAR

idempotency_key VARCHAR UNIQUE

attempt_count INTEGER
max_attempts INTEGER

available_at TIMESTAMPTZ

lease_owner VARCHAR NULL
lease_until TIMESTAMPTZ NULL

last_error_code VARCHAR NULL
last_error_message_redacted TEXT NULL
last_error_at TIMESTAMPTZ NULL

correlation_id VARCHAR
causation_id VARCHAR NULL

created_at
delivered_at NULL

```

Statuses:

```text
PENDING_CONFIGURATION
PENDING
PROCESSING
RETRYABLE
DELIVERED
FAILED_TERMINAL

```

Index:

```text
(status, available_at)

```

Worker claim:

```sql
SELECT *
FROM integration_events
WHERE status IN ('PENDING', 'RETRYABLE')
  AND available_at <= NOW()
  AND (lease_until IS NULL OR lease_until < NOW())
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT :batch_size;

```

---

# 79. Integration inbox

## integration\_inbox

```text
id UUID PK

provider VARCHAR
external_event_id VARCHAR

event_type VARCHAR
schema_version INTEGER NULL

request_hash VARCHAR
signature_verified BOOLEAN

tenant_id UUID NULL

status VARCHAR

payload JSONB

received_at TIMESTAMPTZ
processing_started_at NULL
processed_at NULL

attempt_count INTEGER

last_error_code VARCHAR NULL

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

# 80. Middleware architecture

Every customer/provider form:

```text
Browser
   ↓
BREERO API
   ↓
BREERO DB
 + Outbox
   ↓
COMMIT
   ↓
Background Worker
   ↓
Codestra/Kong
   ↓
external system

```

Never:

```text
Browser → Odoo
Browser → Klyrow
Browser → Telnexa
Browser → n8n

```

---

# 81. System ownership

```text
BREERO PostgreSQL
= marketplace source of truth

Codestra
= integration/control plane

Odoo
= CRM projection

Klyrow
= email delivery

Telnexa
= SMS delivery

n8n
= explicitly approved workflow automation

Stripe
= payment authority after payments are activated

```

Odoo must never overwrite marketplace state.

---

# 82. Event catalog

```text
project_request.created.v1
project_request.updated.v1
project_request.submitted.v1
project_request.qualified.v1
project_request.cancelled.v1

provider_application.submitted.v1
provider.approved.v1
provider.suspended.v1

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

credential.submitted.v1
credential.verified.v1
credential.expiring.v1
credential.expired.v1
credential.revoked.v1

communication.preference_changed.v1

contact_request.created.v1

```

Later:

```text
payment.captured.v1
payment.refunded.v1
payout.created.v1
payout.paid.v1
subscription.activated.v1
subscription.cancelled.v1

```

---

# 83. Standard event envelope

```json
{
  "event_id": "uuid",
  "event_type": "project_request.submitted.v1",
  "schema_version": 1,
  "occurred_at": "2026-08-23T14:30:00Z",

  "aggregate_type": "project_request",
  "aggregate_id": "uuid",
  "aggregate_version": 4,

  "tenant_id": null,
  "legal_entity_id": "uuid",

  "correlation_id": "uuid",
  "causation_id": null,

  "payload": {}
}

```

---

# 84. Runtime capabilities

Public:

```http
GET /api/v2/capabilities

```

Response:

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

Code existing does not imply capability enabled.

---

# 85. Analytics events

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

Analytics must not slow operational transactions.

Prefer outbox/event projection.

---

# 86. Payments — production gated

Implement only after marketplace core passes.

Tables:

```text
payment_intents
payments
payment_events
refunds
platform_fees
provider_balances
provider_ledger_entries
payouts

```

APIs:

```http
POST /api/v2/payments/intents

GET /api/v2/payments/{id}

POST /api/v2/admin/refunds

GET /api/v2/partner/payouts
GET /api/v2/partner/balance

```

Rules:

```text
Stripe webhook is authoritative
browser redirect is not payment authority
all callbacks idempotent
provider payout separate from customer payment
refund audited
payout requires finance permission

```

Until approved:

```text
payments=false
payouts=false

```

---

# 87. Provider subscriptions — gated

Tables:

```text
subscription_plans
provider_subscriptions
subscription_entitlements
subscription_events

```

APIs:

```http
GET /api/v2/partner/subscription
POST /api/v2/partner/subscription/change
POST /api/v2/partner/subscription/cancel

GET /api/v2/admin/subscription-plans
POST /api/v2/admin/subscription-plans
PATCH /api/v2/admin/subscription-plans/{id}

```

Entitlement is separate from authorization.

---

# 88. Database deletion rules

Do not hard-delete:

```text
ProjectRequest
Opportunity history
Quote history
Booking
Job
Credential verification
Review
Payment
Audit event
Outbox/inbox event

```

Use lifecycle status.

For optional related content:

```text
attachments
gallery items
draft objects

```

safe deletion may be allowed according to retention policy.

---

# 89. Foreign-key policy

Prefer:

```text
ON DELETE RESTRICT

```

for business history.

Use:

```text
ON DELETE SET NULL

```

only where losing the optional association does not destroy history.

Avoid cascading deletion through marketplace transactions.

---

# 90. Production migration strategy

Use expand → migrate → contract.

Example:

```text
Migration A
add nullable column

Deploy application supporting old + new

Backfill

Validate data

Migration B
add NOT NULL / constraints

Later remove obsolete fields

```

Every migration PR must prove:

```text
current production head → new head

```

Do not test migrations against production DB.

---

# 91. Database indexes required

At minimum:

```text
project_requests(customer_id, created_at)
project_requests(status, created_at)

provider_organizations(status)
provider_services(service_id, active)

provider_service_areas USING GIST

provider_credentials(provider_id, status, expires_at)

provider_availability_rules(provider_id, weekday)

matching_runs(project_request_id, created_at)
match_candidates(matching_run_id, eligible, rank)

opportunities(provider_id, status, expires_at)
opportunities(project_request_id, status)

lead_connections(project_request_id, provider_id)

quotes(project_request_id, status)
quotes(provider_id, status)

conversations(project_request_id)
messages(conversation_id, created_at)

bookings(project_request_id)
bookings(provider_id, window_start)

jobs(provider_id, status)
jobs(worker_id, status)

reviews(provider_id, created_at)

integration_events(status, available_at)
integration_inbox(provider, external_event_id)

audit_events(resource_type, resource_id, created_at)

```

Use EXPLAIN for high-volume queries before production activation.

---

# 92. API security

All authenticated APIs require:

```text
valid token/session
correct issuer
correct audience
not expired
required permission
tenant/provider ownership
resource state authorization
rate limits

```

Sensitive responses require explicit DTO projection.

Never serialize ORM models blindly.

---

# 93. PII protection

Never expose unmatched-provider access to:

```text
customer email
customer phone
full private address where not needed
private notes
identity documents
payment details

```

Credential documents require protected signed access.

Sensitive logs must redact:

```text
Authorization
Cookie
tokens
passwords
credential numbers
payment details
message content where not necessary

```

---

# 94. Rate limits

Apply suitable limits to:

```text
login
registration
password reset

public request submission
provider application
contact form

message sending
attachment upload

quote mutation

opportunity response

webhooks

admin retries

```

Rate-limit keys should include appropriate combination of:

```text
IP
user
provider
tenant
route

```

---

# 95. Health/operations endpoints

Keep internal/protected:

```http
GET /health/live
GET /health/ready
GET /health/dependencies

```

Readiness should check required dependencies only.

Optional integrations being disabled should not necessarily make the API unhealthy.

---

# 96. Observability

Every request:

```text
request_id
correlation_id
route
method
status
duration
actor safe identifier
tenant safe identifier

```

Domain events:

```text
aggregate
event
status
duration

```

Metrics:

```text
request latency
error rate
DB pool
queue depth
outbox pending
outbox retryable
outbox failed terminal
inbox failures
matching duration
matching no-result rate
quote acceptance
job completion

```

---

# 97. Backend CI

Every backend PR:

```text
Ruff
compileall
pytest

PostgreSQL/PostGIS integration tests

Alembic upgrade tests
schema drift

domain transition tests

RBAC tests
negative authorization tests

idempotency tests
concurrency tests

outbox/inbox tests

OpenAPI generation

dependency/security checks

```

---

# 98. Mandatory negative tests

```text
Provider A cannot read Provider B opportunity
Provider A cannot read Provider B lead
Provider A cannot read Provider B quote
Provider A cannot read Provider B conversation
Provider A cannot read Provider B customer PII
Provider A cannot read Provider B job

Customer A cannot read Customer B ProjectRequest
Customer A cannot read Customer B quote
Customer A cannot read Customer B conversation

Worker cannot execute another provider's job

expired credential cannot match
revoked credential cannot match
suspended provider cannot match

dispatcher cannot approve payout

unmatched provider cannot receive customer contact data

```

---

# 99. Reliability tests

```text
duplicate ProjectRequest submit
→ one logical submission

duplicate opportunity acceptance
→ one LeadConnection

duplicate quote acceptance
→ one accepted quote

duplicate booking command
→ one Booking

duplicate webhook
→ one business effect

worker crashes
→ lease expires
→ safe reclaim

middleware disabled
→ PENDING_CONFIGURATION

middleware enabled
→ PENDING
→ one delivery

retryable integration failure
→ retried

terminal integration failure
→ visible to Ops

expired hold
→ no capacity consumption

```

---

# 100. Backend Definition of Done

Backend Marketplace V2 is complete only when:

```text
ProjectRequest
→ qualification
→ matching
→ eligible providers
→ opportunities
→ provider acceptance
→ LeadConnection
→ conversation
→ quote
→ customer acceptance
→ scheduling
→ Booking
→ worker assignment
→ Job
→ completion
→ verified review

```

works with payments disabled.

Production activation requires all relevant CI, migrations, authorization, idempotency, integration and observability gates to pass.
---

# 101. Shared command and transaction contract

Every externally retryable state-changing command requires:

```text
authenticated actor
tenant and legal-entity context
permission and resource ownership validation
Idempotency-Key and request hash
correlation ID
expected/current aggregate version
explicit state transition
audit entry
versioned outbox event
one atomic database commit
```

Repositories may add and flush but must not independently commit application workflows. State, immutable history, audit and outbox records succeed or fail together.

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

# 102. Codestra/Kong transport contract

Outbound marketplace events must use the transactional outbox and a bounded adapter. The adapter requires TLS, machine credentials with the correct audience, tenant/legal-entity authorization, stable event and idempotency identifiers, correlation IDs, bounded timeouts and retries, structured error mapping and redacted logs.

The protected Codestra boundary requires mTLS, HMAC-V2 request signing where configured, timestamp validation, replay protection and exact tenant, environment and scope checks. Browser clients never call Codestra, Odoo, Klyrow, Telnexa or n8n directly.

Inbound callbacks must authenticate, verify signature and timestamp, reject replay, deduplicate by `(provider, external_event_id)`, authorize tenant scope, process idempotently and audit the outcome.

---

# 103. Communication preference and compliance contract

Communication preferences must distinguish transactional email, transactional SMS, marketing email and marketing SMS. Store purpose, channel, disclosure/policy version, source, timestamp and suppression state.

Explicit re-opt-in may clear only the matching channel-and-purpose suppression. Marketing consent must never be inferred from transactional consent, account creation, a service request or provider onboarding.

---

# 104. Required completion evidence for every backend PR

Every backend PR description must report:

```text
BASE_SHA
FINAL_SHA
ALEMBIC_PREVIOUS_HEAD
ALEMBIC_NEW_HEAD
MIGRATION_UPGRADE
MIGRATION_DOWNGRADE
POSTGRES_POSTGIS_TESTS
UNIT_TESTS
AUTH_AND_NEGATIVE_AUTH_TESTS
IDEMPOTENCY_TESTS
CONCURRENCY_TESTS
OPENAPI_AND_COMPATIBILITY
OUTBOX_INBOX_TESTS
FEATURE_FLAGS_ENABLED
PRODUCTION_DB_TOUCHED
KNOWN_RISKS
ROLLBACK
```

A capability remains disabled merely because its schema, endpoint or worker exists.
