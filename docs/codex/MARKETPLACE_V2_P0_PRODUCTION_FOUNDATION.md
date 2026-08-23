# BREERO Marketplace V2 — P0 Production Foundation and Security Gates

## Verified baseline

Verified on 2026-08-23 against [PR #35](https://github.com/appolon1908-hue/Breero.com/pull/35), open Draft at head `503210976956436f35844ee9f5c36a8e0b1717f1`, and the actual authentication, capability, application-mount and production-configuration code on `codex/marketplace-v2-release-safety`.

PR #35 establishes a green request-only foundation but intentionally introduces no Marketplace V2 aggregate or schema. The current API mounts `/api/v1` only. Registration fails closed when Keycloak is enabled, while login and refresh still issue local credentials. Keycloak request authentication resolves a local user by verified email and compares one local role with realm roles rather than binding durable issuer/subject identity.

These are P0 production prerequisites, not proof that the Marketplace V2 features are implemented.

## Safety boundary

This document is planning authority only and must not be deployed. Preserve request-only/manual dispatch. Keep Marketplace V2, payments, payouts, paid leads, instant booking, automatic assignment/confirmation, marketing and unrestricted communications disabled.

The canonical Keycloak issuer is `https://auth.codestra.co/realms/codestra`; `auth.codestra.agency` is deprecated.

# A. BACKEND PRODUCTION TRACK

Backend owns:

```text
FastAPI
PostgreSQL/PostGIS
Alembic
Authentication
Authorization
RBAC
Capability gates
Idempotency
Domains
Matching
Scheduling
Outbox/inbox
Codestra middleware
OpenAPI
Backend CI
```

No Next.js/React work belongs on backend branches.

## Backend branches

```text
be/marketplace-v2-p0-api-foundation
be/marketplace-v2-p0-production-schema
be/marketplace-v2-p0-keycloak-authentication
be/marketplace-v2-p0-record-authorization
be/marketplace-v2-p0-capability-gating
be/marketplace-v2-p0-idempotency

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

One Draft PR per branch. The first six are production prerequisites.

---

# P0-01 — Complete `/api/v2` foundation

Do not create fake `501 Not Implemented` production routes.

Create:

```text
apps/api/app/api/v2/

router.py

public.py
catalog.py

project_requests.py
providers.py

customer.py
partner.py
worker.py

matching.py
opportunities.py
quotes.py
conversations.py

bookings.py
jobs.py
reviews.py

operations.py
admin.py

integrations.py
analytics.py
```

Mount:

```python
app.include_router(api_v2_router, prefix="/api/v2")
```

Recommended top-level contract:

```text
/api/v2/public
/api/v2/catalog

/api/v2/project-requests
/api/v2/providers

/api/v2/customer
/api/v2/partner
/api/v2/worker

/api/v2/matching
/api/v2/opportunities
/api/v2/quotes
/api/v2/conversations

/api/v2/bookings
/api/v2/jobs
/api/v2/reviews

/api/v2/ops
/api/v2/admin

/api/v2/integrations
/api/v2/analytics
```

Keep `/api/v1` alive during migration.

---

# Complete V2 API inventory

## Public

```http
GET  /api/v2/capabilities

POST /api/v2/public/contact-requests
POST /api/v2/public/provider-applications
POST /api/v2/public/communication-preferences
```

## Catalog

```http
GET /api/v2/catalog/categories
GET /api/v2/catalog/categories/{slug}

GET /api/v2/catalog/services
GET /api/v2/catalog/services/{slug}
GET /api/v2/catalog/services/{id}/questions
```

## ProjectRequest

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
GET /api/v2/project-requests/{id}/availability
```

## Public provider marketplace

```http
GET /api/v2/providers
GET /api/v2/providers/{slug}

GET /api/v2/providers/{slug}/services
GET /api/v2/providers/{slug}/reviews
GET /api/v2/providers/{slug}/service-area
GET /api/v2/providers/{slug}/availability-summary
```

## Customer portal

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

## Provider portal

```http
GET /api/v2/partner/dashboard

GET   /api/v2/partner/profile
PATCH /api/v2/partner/profile

GET /api/v2/partner/onboarding
PATCH /api/v2/partner/onboarding
POST /api/v2/partner/onboarding/submit

GET /api/v2/partner/services
PUT /api/v2/partner/services

GET    /api/v2/partner/service-areas
POST   /api/v2/partner/service-areas
PATCH  /api/v2/partner/service-areas/{id}
DELETE /api/v2/partner/service-areas/{id}

GET  /api/v2/partner/workers
POST /api/v2/partner/workers
GET /api/v2/partner/workers/{id}
PATCH /api/v2/partner/workers/{id}

GET /api/v2/partner/availability
PUT /api/v2/partner/availability

POST   /api/v2/partner/availability/exceptions
PATCH  /api/v2/partner/availability/exceptions/{id}
DELETE /api/v2/partner/availability/exceptions/{id}

GET  /api/v2/partner/credentials
POST /api/v2/partner/credentials
GET /api/v2/partner/credentials/{id}
PATCH /api/v2/partner/credentials/{id}

POST /api/v2/partner/credentials/{id}/documents

GET /api/v2/partner/opportunities
GET /api/v2/partner/opportunities/{id}

POST /api/v2/partner/opportunities/{id}/view
POST /api/v2/partner/opportunities/{id}/accept
POST /api/v2/partner/opportunities/{id}/decline

GET /api/v2/partner/leads
GET /api/v2/partner/leads/{id}

GET /api/v2/partner/quotes
GET /api/v2/partner/quotes/{id}

POST /api/v2/partner/project-requests/{id}/quotes
PATCH /api/v2/partner/quotes/{id}

POST /api/v2/partner/quotes/{id}/send
POST /api/v2/partner/quotes/{id}/revise
POST /api/v2/partner/quotes/{id}/withdraw

GET /api/v2/partner/jobs
GET /api/v2/partner/jobs/{id}

GET /api/v2/partner/customers
GET /api/v2/partner/customers/{id}

GET /api/v2/partner/reviews
POST /api/v2/partner/reviews/{id}/response

GET /api/v2/partner/analytics/overview
GET /api/v2/partner/analytics/funnel
GET /api/v2/partner/analytics/jobs
GET /api/v2/partner/analytics/revenue
```

## Worker portal

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

## Conversations

```http
GET /api/v2/conversations
GET /api/v2/conversations/{id}

GET /api/v2/conversations/{id}/messages

POST /api/v2/conversations/{id}/messages
POST /api/v2/conversations/{id}/attachments

POST /api/v2/conversations/{id}/read
```

## Quotes

```http
GET /api/v2/quotes/{id}

POST /api/v2/quotes/{id}/accept
POST /api/v2/quotes/{id}/decline
```

## Booking

```http
GET /api/v2/bookings/{id}
GET /api/v2/bookings/{id}/timeline

POST /api/v2/bookings/{id}/confirm
POST /api/v2/bookings/{id}/reschedule-request
POST /api/v2/bookings/{id}/cancel
```

## Jobs

```http
GET /api/v2/jobs/{id}
GET /api/v2/jobs/{id}/timeline

POST /api/v2/jobs/{id}/en-route
POST /api/v2/jobs/{id}/arrive
POST /api/v2/jobs/{id}/start
POST /api/v2/jobs/{id}/complete

POST /api/v2/jobs/{id}/notes
POST /api/v2/jobs/{id}/evidence
POST /api/v2/jobs/{id}/additional-work
```

## Reviews

```http
POST /api/v2/jobs/{id}/review
GET  /api/v2/reviews/{id}
```

## Operations

```http
GET /api/v2/ops/project-requests
GET /api/v2/ops/project-requests/{id}

POST /api/v2/ops/project-requests/{id}/qualify
POST /api/v2/ops/project-requests/{id}/mark-unserviceable

POST /api/v2/ops/project-requests/{id}/matching-runs

GET /api/v2/ops/matching-runs/{id}
GET /api/v2/ops/matching-runs/{id}/candidates

POST /api/v2/ops/project-requests/{id}/opportunities
POST /api/v2/ops/opportunities/{id}/withdraw

GET /api/v2/ops/jobs
GET /api/v2/ops/jobs/{id}

POST /api/v2/ops/jobs/{id}/assign
POST /api/v2/ops/jobs/{id}/reassign
POST /api/v2/ops/jobs/{id}/cancel

GET /api/v2/ops/providers
GET /api/v2/ops/providers/{id}

GET /api/v2/ops/exceptions
GET /api/v2/ops/exceptions/{id}

POST /api/v2/ops/exceptions/{id}/acknowledge
POST /api/v2/ops/exceptions/{id}/resolve

GET /api/v2/ops/integration-events
GET /api/v2/ops/integration-failures

POST /api/v2/ops/integration-events/{id}/retry
```

## Admin

```http
GET /api/v2/admin/users
GET /api/v2/admin/users/{id}

GET /api/v2/admin/roles
GET /api/v2/admin/permissions

PUT /api/v2/admin/users/{id}/roles

GET /api/v2/admin/provider-applications
GET /api/v2/admin/provider-applications/{id}

POST /api/v2/admin/provider-applications/{id}/approve
POST /api/v2/admin/provider-applications/{id}/reject
POST /api/v2/admin/provider-applications/{id}/request-information

GET /api/v2/admin/providers
GET /api/v2/admin/providers/{id}

POST /api/v2/admin/providers/{id}/approve
POST /api/v2/admin/providers/{id}/suspend
POST /api/v2/admin/providers/{id}/reactivate

GET /api/v2/admin/credentials
GET /api/v2/admin/credentials/{id}

POST /api/v2/admin/credentials/{id}/verify
POST /api/v2/admin/credentials/{id}/reject
POST /api/v2/admin/credentials/{id}/revoke

GET /api/v2/admin/features
GET /api/v2/admin/features/{key}
PUT /api/v2/admin/features/{key}

GET /api/v2/admin/audit-events
GET /api/v2/admin/audit-events/{id}

GET /api/v2/admin/reviews
POST /api/v2/admin/reviews/{id}/moderate
```

---

# P0-02 — Production database migrations

PR #35 reports current Alembic head as `017_provider_credentials`; V2 should therefore continue additively from that exact verified head. ([PR #35](https://github.com/appolon1908-hue/Breero.com/pull/35))

I would use:

```text
018_identity_access_v2
019_project_requests_v2
020_catalog_questionnaire_v2
021_provider_marketplace_v2
022_provider_trust_availability_v2
023_matching_opportunities_v2
024_quotes_conversations_v2
025_booking_job_review_v2
026_idempotency_audit_v2
027_integration_inbox_outbox_v2
028_analytics_v2
```

Do not hard-code those revision IDs if the repository head changes before implementation.

## 018 — Identity/access

Add:

```text
external_identities
provider_members
user_permissions / role mappings if needed
```

### external\_identities

```text
id UUID PK

user_id UUID FK

issuer VARCHAR NOT NULL
subject VARCHAR NOT NULL

email_at_link_time VARCHAR NULL

created_at
last_seen_at

UNIQUE(issuer, subject)
```

This fixes an important current weakness: Keycloak lookup currently resolves the user by the email claim.

Identity must be:

```text
issuer + subject
```

not email.

---

## 019 — ProjectRequest

```text
project_requests
project_request_answers
project_request_attachments
project_request_status_history
customer_properties
```

---

## 020 — Questionnaire

```text
service_categories
service_questions
service_question_options
service_question_rules
```

Extend existing `services`.

---

## 021 — Provider marketplace

```text
provider_organizations
provider_profiles
provider_members
provider_workers
provider_services
provider_service_areas
provider_gallery
provider_applications
provider_application_status_history
```

---

## 022 — Trust / availability

```text
credential_requirements
provider_credentials
credential_verifications
provider_documents

provider_availability_rules
provider_availability_exceptions
```

---

## 023 — Matching

```text
matching_runs
match_candidates
match_reasons

opportunities
opportunity_status_history
lead_connections
```

---

## 024 — Commercial / conversations

```text
quotes
quote_versions
quote_line_items
quote_status_history

conversations
conversation_participants
messages
message_attachments
message_receipts
```

---

## 025 — Fulfillment/reviews

Add nullable V2 references to existing booking/job records.

```text
bookings.project_request_id
bookings.accepted_quote_id

job_assignments
job_status_history

reviews
review_dimensions
review_responses
review_moderation
```

Never destructively rewrite old booking/job history.

---

## 026 — Production command controls

```text
idempotency_records
audit_events
```

---

## 027 — Integration reliability

```text
integration_inbox
```

Extend existing outbox for:

```text
lease_owner
lease_until
correlation_id
causation_id
schema_version
```

---

# Database production rules

Use:

```text
UUID primary keys
TIMESTAMPTZ timestamps
BIGINT minor units for money
CHAR(3) currency
JSONB only for genuinely flexible payloads
PostGIS GEOGRAPHY for location
```

Never money as `float`.

Add version fields to major aggregates:

```text
project_requests.version
opportunities.version
quotes.version
bookings.version
jobs.version
```

Use optimistic concurrency.

Use foreign keys.

Prefer:

```text
ON DELETE RESTRICT
```

for transactional history.

Do not cascade-delete:

```text
ProjectRequest
Opportunity
Quote
Booking
Job
Review
Payment
Audit
Integration event
```

---

# P0-03 — Real authentication

This needs tightening before Marketplace V2.

Current configuration supports Keycloak but also local JWT secrets and local login.

For production, use:

```text
Keycloak
OIDC
Authorization Code + PKCE for users
Client Credentials for services
```

## Production rule

```text
APP_ENV=production
AUTH_MODE=keycloak
```

Fail startup if production uses local password authentication.

Do not allow:

```text
/api/v1/auth/login
/api/v1/auth/register
local refresh-token issuance
```

as primary production authentication when Keycloak mode is active.

The current `/login` path still invokes local `AuthService.login()` regardless of `keycloak_enabled`; that is something the P0 auth branch should remove from the production path.

## Verify JWT claims

Every token must validate:

```text
signature
iss
aud
azp where applicable
exp
nbf
iat
sub
```

Also enforce configured algorithm.

Never trust unverified token claims.

## JWKS

Implement:

```text
Keycloak issuer
       ↓
OpenID discovery
       ↓
jwks_uri
       ↓
cached keys
```

Support rotation.

Unknown `kid`:

```text
refresh JWKS once
→ retry validation
→ reject
```

Never permanently cache an unknown key failure.

---

# User linking

Do not:

```python
user = repository.by_email(claims["email"])
```

as the production identity anchor.

Instead:

```python
identity = await identities.by_issuer_subject(
    issuer=claims["iss"],
    subject=claims["sub"],
)
```

Then:

```text
external identity
      ↓
local Breero User
      ↓
customer/provider/worker membership
```

Email may change.

`sub` should remain the identity.

---

# Authentication context

Create:

```python
@dataclass(frozen=True)
class Principal:
    user_id: UUID
    issuer: str
    subject: str
    roles: frozenset[str]
    permissions: frozenset[str]
    provider_ids: frozenset[UUID]
    worker_id: UUID | None
    tenant_id: UUID | None
    legal_entity_ids: frozenset[UUID]
```

Every protected endpoint consumes `Principal`.

---

# P0-04 — Record-level authorization

Role checking alone is not enough.

Current auth dependency primarily checks one `UserRole`/realm role mapping.

Marketplace V2 requires:

```text
RBAC
+
resource ownership
+
provider membership
+
assignment
+
tenant/legal entity
+
state
```

## Authorization architecture

```text
Authentication
      ↓
Principal
      ↓
Permission
      ↓
Record policy
      ↓
Domain command
```

Create:

```text
apps/api/app/domains/authorization/

permissions.py
principal.py
policies.py
dependencies.py
```

---

# Customer policies

A customer can access a request only when:

```text
project_request.customer_id
==
principal.customer_id
```

Apply similarly to:

```text
Quote
Conversation
Booking
Job
Review
Property
```

---

# Provider policies

A provider user requires:

```text
provider_members.provider_id == resource.provider_id

AND

provider_members.status == ACTIVE
```

and required permission.

Provider A cannot access Provider B:

```text
Opportunity
Lead
Quote
Conversation
Customer relationship
Booking
Job
Credential
Analytics
```

---

# Worker policies

Worker can access:

```text
job.worker_id == principal.worker_id
```

or explicitly assigned permitted team context.

Worker does not inherit provider-owner authority.

---

# Ops/admin

Operations still requires granular permission.

Example:

```text
DISPATCHER
job.assign

TRUST_SAFETY
credential.verify
provider.suspend

FINANCE
refund.create
payout.approve
```

Dispatcher must not get finance authority.

---

# Repository-level filtering

Avoid:

```python
row = await repository.by_id(id)

if row.provider_id != principal.provider_id:
    raise Forbidden()
```

when possible.

Prefer:

```python
row = await repository.by_id_for_provider(
    id,
    provider_id=provider_id,
)
```

SQL includes ownership predicate.

This reduces cross-tenant leakage.

---

# Required negative tests

```text
Customer A → Customer B request = denied

Provider A → Provider B opportunity = denied
Provider A → Provider B lead = denied
Provider A → Provider B quote = denied
Provider A → Provider B conversation = denied
Provider A → Provider B job = denied
Provider A → Provider B customer = denied

Worker A → unassigned job = denied

Dispatcher → payout approval = denied

Support → credential verification = denied
```

Run these against real PostgreSQL.

---

# P0-05 — Capability gating

PR #35 added the public effective capability projection and production defaults remain false. ([PR #35](https://github.com/appolon1908-hue/Breero.com/pull/35))

That is only half the job.

The backend must enforce capabilities too.

## Capability registry

Create:

```text
apps/api/app/domains/capabilities/

models.py
registry.py
dependencies.py
service.py
schemas.py
```

Recommended effective capability:

```python
@dataclass(frozen=True)
class Capability:
    name: str
    enabled: bool
    reason: str | None
```

## Server guard

```python
def require_capability(name: str):
    async def dependency(
        capabilities: CapabilityRegistry = Depends(get_capabilities),
    ):
        if not capabilities.enabled(name):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "CAPABILITY_DISABLED",
                    "capability": name,
                },
            )
    return dependency
```

Then:

```python
@router.post(
    "/{request_id}/matching-runs",
    dependencies=[Depends(require_capability("marketplace_matching"))],
)
```

Use on every protected feature.

---

# Capability matrix

```text
request_intake
→ ProjectRequest create/submit

provider_self_service
→ partner profile/services/workforce APIs

marketplace_matching
→ matching runs

provider_opportunities
→ opportunity delivery/respond

quotes
→ quote APIs

messaging
→ conversation message APIs

reviews
→ review APIs

instant_booking
→ direct booking path

automatic_assignment
→ automatic dispatch

payments
→ payment mutations

payouts
→ provider payout APIs

paid_leads
→ lead-purchase model

marketing
→ marketing sends
```

---

# Effective capability

Do not expose raw environment flags directly.

Calculate:

```text
CODE_AVAILABLE
AND
ENVIRONMENT_FLAG
AND
DEPENDENCY_FLAGS
AND
RELEASE_POLICY
```

Example:

```python
quotes = (
    settings.marketplace_quotes_enabled
    and provider_self_service
    and request_intake
)
```

Payment:

```python
payments = (
    settings.payments_enabled
    and settings.stripe_enabled
    and settings.online_checkout_enabled
)
```

That is consistent with the composite-capability approach already introduced by PR #35. ([PR #35](https://github.com/appolon1908-hue/Breero.com/pull/35))

---

# P0-06 — Production idempotency

Do not rely only on frontend button disabling.

Add:

```text
idempotency_records
```

Schema:

```text
id UUID PK

actor_key VARCHAR
operation VARCHAR
idempotency_key VARCHAR

request_hash VARCHAR

status VARCHAR

resource_type VARCHAR NULL
resource_id UUID NULL

response_code INTEGER NULL
response_json JSONB NULL

created_at
updated_at
expires_at

UNIQUE(actor_key, operation, idempotency_key)
```

States:

```text
IN_PROGRESS
COMPLETED
FAILED
```

---

# Idempotency architecture

Use two layers.

### HTTP middleware

Validates:

```text
Idempotency-Key present
reasonable length
valid character set
mutating route requires it
```

Sets:

```python
request.state.idempotency_key
```

### Domain idempotency service

Owns transactional correctness.

```python
record = await idempotency.acquire(
    actor_key=principal.identity_key,
    operation="quote.accept",
    key=request.state.idempotency_key,
    request_hash=hash_request(payload),
)
```

Rules:

```text
new key
→ create IN_PROGRESS
→ execute command
→ save resource + outbox + COMPLETED
→ commit

same key + same hash + COMPLETED
→ return original response

same key + different hash
→ 409 IDEMPOTENCY_KEY_REUSED

same key + IN_PROGRESS
→ 409/425 REQUEST_IN_PROGRESS
```

---

# Commands requiring idempotency

At minimum:

```text
ProjectRequest submit

Provider application submit

Opportunity accept
Opportunity decline

Quote send
Quote revise
Quote accept
Quote decline

Message send where external duplicate is meaningful

Booking confirm
Booking cancel

Job assign
Job state change
Job complete

Review submit

Integration retry

Payment intent
Refund
Payout
```

---

# Critical transaction rule

This must happen atomically:

```text
business state
+
audit event
+
outbox event
+
idempotency completion
```

One PostgreSQL commit.

Otherwise:

```text
business succeeded
but idempotency failed
```

can create duplicates.

---

# Backend middleware integration

Every form should follow:

```text
Frontend
   ↓
Breero API
   ↓
Domain transaction
   ├── business records
   ├── audit
   ├── idempotency
   └── outbox
   ↓
COMMIT
   ↓
return success
   ↓
worker
   ↓
Codestra/Kong
```

Never:

```text
Frontend
→ Codestra
→ Odoo
```

---

# Codestra boundary

```text
BREERO
Marketplace source of truth

Codestra
Integration/control plane

Odoo
CRM projection

Klyrow
Email delivery

Telnexa
SMS delivery

n8n
Approved automation
```

Your current production configuration already includes middleware URL, CA, client certificate/key, HMAC identity, audience, tenant and scope fields, so the repository is already pointed toward this authenticated middleware pattern.

---

# Integration events

All important mutations emit versioned events:

```text
project_request.submitted.v1

provider_application.submitted.v1

matching.completed.v1

opportunity.sent.v1
opportunity.accepted.v1

lead.connected.v1

quote.sent.v1
quote.accepted.v1

conversation.message_sent.v1

booking.confirmed.v1

job.assigned.v1
job.en_route.v1
job.started.v1
job.completed.v1

review.submitted.v1

credential.submitted.v1
credential.verified.v1
credential.expired.v1
```

---

# Backend P0 Definition of Done

P0 is not complete until:

```text
/api/v2 mounted
all V2 routers contract-tested

migrations 017 → new head pass

empty DB → head passes

Keycloak required in production

local production login disabled

JWT issuer/audience/signature tested

issuer+subject identity binding implemented

record-level authorization implemented

negative tenant tests pass

capability guards server-side

all dangerous features default false

idempotency transactional

OpenAPI generated

PostgreSQL/PostGIS tests pass

Codestra outbox remains durable

no production DB touched by CI
```

---

# B. FRONTEND PRODUCTION TRACK

Keep this completely separate from backend.

Frontend owns:

```text
apps/web
apps/partner
apps/ops
apps/admin

packages/ui
packages/types
packages/api-client
```

Frontend does **not** own authentication truth, authorization truth, capabilities, matching, scheduling or integration state.

## Frontend branches

```text
fe/marketplace-v2-p0-api-client
fe/marketplace-v2-p0-production-auth
fe/marketplace-v2-p0-capability-provider
fe/marketplace-v2-p0-idempotent-forms
fe/marketplace-v2-p0-access-error-boundaries

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

---

# FE-P0-01 — Typed V2 client

All portal calls go through:

```text
packages/api-client
```

Do not scatter:

```ts
fetch("/api/v2/...")
```

through pages.

Target:

```ts
interface BreeroApiV2 {
  public: PublicApi;
  catalog: CatalogApi;

  projectRequests: ProjectRequestApi;
  providers: ProviderApi;

  customer: CustomerApi;
  partner: PartnerApi;
  worker: WorkerApi;

  quotes: QuoteApi;
  conversations: ConversationApi;

  bookings: BookingApi;
  jobs: JobApi;
  reviews: ReviewApi;

  ops: OpsApi;
  admin: AdminApi;
}
```

Generate/update from backend OpenAPI where practical.

---

# FE-P0-02 — Real frontend authentication

Use Keycloak OIDC:

```text
Authorization Code
+
PKCE
```

Preferred browser design:

```text
Browser
   ↓
Next.js/BFF session
   ↓
HttpOnly Secure SameSite cookie
   ↓
Breero API token forwarding
```

Avoid storing long-lived tokens in:

```text
localStorage
sessionStorage
```

Never put refresh tokens in client-readable JavaScript storage.

Frontend routes may hide inaccessible pages for UX, but backend authorization remains authoritative.

---

# Portal auth requirements

Customer:

```text
/customer/*
```

Provider:

```text
/partner/*
```

Worker:

```text
/worker/*
```

Ops:

```text
/ops/*
```

Admin:

```text
/admin/*
```

Each portal reads effective principal/session.

Do not trust client-side role claims alone.

---

# FE-P0-03 — Capability Provider

Create:

```text
packages/ui/providers/CapabilityProvider
```

Fetch:

```http
GET /api/v2/capabilities
```

Fail closed.

Example:

```tsx
<CapabilityGate capability="quotes">
  <CreateQuoteButton />
</CapabilityGate>
```

Unavailable capabilities render:

```text
hidden
or
explicit unavailable state
```

depending on UX.

Never default missing capability to true.

---

# FE-P0-04 — Idempotent forms

Every logical command gets one stable key.

Example:

```ts
const key = crypto.randomUUID();
```

Keep the same key across:

```text
retry
network timeout
button re-enable
```

Generate a new key only for a **new logical action**.

API client:

```ts
await api.quotes.accept(id, {
  idempotencyKey,
});
```

Do not generate a fresh key on every retry.

---

# Forms needing idempotency

```text
ProjectRequest submit

Provider onboarding submit

Opportunity accept/decline

Quote send
Quote accept/decline

Booking confirm/cancel

Job transitions

Review submit

Admin manual retry

Payments later
```

---

# FE-P0-05 — Authorization/error boundaries

Create common UI:

```text
Unauthenticated
Forbidden
NotFound
Conflict
RateLimited
TemporarilyUnavailable
NetworkOffline
```

API mapping:

```text
401 → login/session recovery
403 → forbidden
404 → missing/not-visible
409 → stale/idempotency/state conflict
422 → field validation
429 → retry later
5xx → temporary failure
```

A frontend route guard is not authorization.

---

# Customer frontend features

```text
Homepage
Service discovery

ProjectRequest wizard
Dynamic questionnaire
Attachments
Address/property
Timing

Request dashboard
Matched providers
Provider profiles

Quote comparison
Messaging

Booking
Job tracking
Reviews

Profile
Properties
Communication preferences
Contact form
```

All have explicit `/api/v2` endpoints listed above.

---

# Provider frontend features

```text
Onboarding

Dashboard
Profile
Services
Service areas

Workers
Availability
Credentials

Opportunities
Leads

Quotes
Messaging

Schedule
Jobs
Customers

Reviews
Analytics
```

All consume partner/marketplace V2 APIs.

---

# Worker frontend features

```text
Dashboard
Schedule
Assigned jobs

En route
Arrived
Start
Complete

Notes
Evidence

Availability
Credentials
```

---

# Ops frontend features

```text
Requests
Qualification

Matching inspector
Opportunities

Jobs
Assignments

Providers
Exceptions

Integration failures
Analytics
Map
```

---

# Admin frontend features

```text
Provider applications

Providers
Credential verification

Users
Roles
Permissions

Catalog

Feature capabilities

Reviews
Audit

Integrations
```

---

# Frontend form integration rule

Every form:

```text
User
 ↓
Frontend
 ↓
Typed /api/v2 client
 ↓
BREERO backend
 ↓
PostgreSQL
 ↓
success
```

Middleware delivery happens after backend commit.

The user should not lose a request because Odoo/Klyrow/Codestra is temporarily unavailable.

---

# Production form test matrix

Every critical form should test:

```text
happy path

required validation
invalid value

401
403
404
409
422
429

500
503

network timeout
retry

double click

refresh
back navigation

mobile
keyboard
screen reader
```

---

# Git merge order

Keep frontend/backend clean by landing backend contract first.

```text
BE P0-01 API foundation
        ↓
BE P0-02 DB
        ↓
BE P0-03 Auth
        ↓
BE P0-04 Record authorization
        ↓
BE P0-05 Capabilities
        ↓
BE P0-06 Idempotency
        ↓
──────── P0 SECURITY GATE ────────
        ↓
BE marketplace domains
        ↓
FE typed API client
        ↓
FE feature pages/forms
```

For individual domains:

```text
BE ProjectRequest
→ merge
→ FE Request Wizard

BE Provider
→ merge
→ FE Provider Portal

BE Matching
→ merge
→ FE Customer Matches + Ops Inspector

BE Quotes
→ merge
→ FE Quote Builder + Quote Comparison

BE Messaging
→ merge
→ FE Messaging

BE Jobs
→ merge
→ FE Provider/Worker/Customer Job UI
```

This prevents frontend branches from depending on speculative APIs.

---

# Production release gate

I would not call Marketplace V2 production-ready until this real end-to-end path passes:

```text
Keycloak login
   ↓
Customer ProjectRequest
   ↓
Questionnaire
   ↓
Address/photo/timing
   ↓
Submit with idempotency
   ↓
Record authorization
   ↓
Qualification
   ↓
Matching
   ↓
3 eligible providers
   ↓
Opportunities
   ↓
Provider accepts
   ↓
LeadConnection
   ↓
Conversation
   ↓
Quote
   ↓
Customer accepts
   ↓
Booking
   ↓
Worker assignment
   ↓
Job
   ↓
Completion
   ↓
Verified review
```

and simultaneously proves:

```text
cross-customer isolation
cross-provider isolation
worker assignment isolation

invalid issuer denied
invalid audience denied
expired token denied
wrong role denied

capability disabled denied server-side

duplicate command creates one effect

expired credential cannot match

Codestra offline does not lose transaction

outbox retries once safely

payments remain inaccessible while disabled
```

That is the point where Breero stops being merely “architecture-defined” and becomes a genuinely production-ready Marketplace V2 backend/frontend system.
