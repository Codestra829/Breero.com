# BREERO Feature, API, Forms, CTA, and Docker Production Mission

## Mission status

```text
DOCUMENT_TYPE=IMPLEMENTATION_AND_RELEASE_MISSION
ACCEPTED_MAIN_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
ACCEPTED_ALEMBIC_HEAD=017_provider_credentials
PRODUCTION_DEPLOYED=NO
MARKETPLACE_V2=NO_GO
PRODUCTION_READY=NO
```

This mission improves the existing BREERO monorepo. It does not authorize a rewrite, a new unrelated repository, a direct push to `main`, an unsafe mega-branch, or early capability activation.

The current accepted release remains quote-only request intake with operator-confirmed manual scheduling and financial/external automation disabled.

## Immediate repository findings that must be addressed

1. The frontend deployment boundary contained the retired Keycloak issuer `auth.codestra.agency`; PR #46 moves deployable frontend configuration to the canonical issuer `https://auth.codestra.co/realms/codestra` and adds Docker validation.
2. Public service, contact, and provider-interest forms are concentrated in one large component with duplicated configuration and generic error handling.
3. The browser creates a new idempotency key for every retry, which can create a second submission after an ambiguous network failure.
4. The Next.js API proxy drops useful backend headers such as request/correlation identifiers and retry information.
5. CTA copy says “Book” while the accepted release is request-first and operator-confirmed.
6. The backend exposes a useful V1 surface, but route naming, command requirements, error/header behavior, generated client coverage, and lifecycle ownership need one reviewed contract.
7. Two production backend Compose definitions exist and must not remain competing production authorities.
8. The active ruleset/check defect is tracked by issue #45.
9. Production infrastructure/UAT blockers remain issues #17, #18, and #19 and require fresh evidence.

# 1. Non-negotiable branch policy

Every heavy feature receives its own branch and draft PR. Create each branch from the latest human-merged `main`, not from another unmerged feature branch, unless the PR is explicitly a temporary stacked review and is rebased before merge.

Do not create one permanent “finish everything” branch.

Required branch sequence:

```text
0. ci/required-check-governance
1. be/marketplace-v2-p0-api-foundation              # existing PR #38
2. be/auth-identity-tenancy-rbac
3. be/api-contract-cleanup
4. be/public-submissions-hardening
5. fe/public-forms-cta-hardening
6. integration/outbox-inbox-webhooks
7. be/documents-private-storage
8. be/provider-network
9. be/matching-opportunities
10. be/quotes-conversations
11. be/booking-job-operations
12. fe/customer-portal
13. fe/provider-worker-portals
14. fe/ops-admin-portals
15. integration/odoo-kong-n8n-klyrow-telnexa
16. ci/docker-release-platform
17. release/isolated-staging-certification
18. release/production-candidate
```

Financial work remains later and separate:

```text
be/payments-refunds
be/provider-earnings-payouts
```

Do not start those branches until identity, authorization, capability enforcement, idempotency, concurrency, audit, outbox, inbox, webhooks, storage, reconciliation, and finance governance are independently accepted.

## Per-branch rules

Every branch must:

- have one primary responsibility;
- contain no unrelated formatting sweep;
- preserve V1 compatibility unless the PR contains a reviewed migration/deprecation plan;
- regenerate OpenAPI and typed contracts when the API changes;
- add positive, negative, failure, authorization, idempotency, and concurrency evidence as applicable;
- state every capability affected and prove disabled capabilities remain disabled;
- open as a draft PR;
- report starting `main` SHA, final head SHA, migrations, tests, workflow runs, unresolved risks, and rollback boundary;
- never deploy merely because CI is green.

# 2. Phase 0 — fix governance and current reviews

Before new heavy feature implementation:

1. Finish current exact-head review repairs on PRs #38–#43.
2. Resolve issue #45 with one unambiguous required `quality` aggregator that runs for backend-only, frontend-only, mixed, workflow-only, and documentation-only PRs.
3. Preserve one approval, last-push approval, and resolved-thread requirements.
4. Do not bypass the ruleset.
5. Review and merge PR #46 only after its dedicated Docker gate passes and independent review approves the unchanged head.

# 3. Authentication, identity, tenancy, and RBAC branch

Branch:

```text
be/auth-identity-tenancy-rbac
```

Implement only:

- canonical issuer `https://auth.codestra.co/realms/codestra`;
- Authorization Code + PKCE S256 for humans;
- client credentials for registered machines;
- signature, algorithm, issuer, audience, azp, exp, nbf, iat, subject, and kid validation;
- process-wide discovery/JWKS cache;
- unknown-kid refresh once, then deny;
- immutable `(issuer, subject)` external identity mapping;
- local production login shutdown;
- local users, tenants/legal entities, memberships, roles, and explicit permissions;
- server-constructed Principal;
- `/api/v2/me` and authenticated context projection;
- record-level tenant/legal-entity denial;
- no wildcard admin role.

Mandatory negative tests include wrong issuer/audience/azp/algorithm, expired/not-yet-valid tokens, missing token, unknown kid, inactive membership, cross-tenant access, and local production login denial.

# 4. API contract cleanup branch

Branch:

```text
be/api-contract-cleanup
```

## Goals

Create one authoritative API contract without breaking accepted V1 consumers.

Implement:

- one API route registry with owner, audience, authentication, permission, capability, idempotency, version/ETag, request/response schema, emitted event, and deprecation status;
- stable operation IDs;
- consistent plural resource naming;
- consistent error envelope for V2;
- preservation of `WWW-Authenticate`, `Retry-After`, `Allow`, `ETag`, request ID, and correlation ID;
- typed pagination and filtering conventions;
- request/correlation middleware with validation before reflection;
- OpenAPI drift gate;
- generated TypeScript client or validated shared client definitions;
- API compatibility tests proving existing V1 routes still work;
- explicit `/internal` denial at public ingress;
- machine endpoint allowlists;
- rate-limit response contract;
- deprecation headers and documented transition when an alias is replaced.

## State-changing command requirements

Every state mutation must require, as applicable:

```text
authentication
permission
tenant/legal-entity scope
record policy
runtime capability
Idempotency-Key
canonical request hash
request ID
correlation ID
If-Match/version
valid state transition
audit
transactional outbox
```

Do not let routers directly own business rules or call external providers inside the authoritative PostgreSQL transaction.

# 5. Current public API readiness

The following public/account APIs must be fully documented, generated into OpenAPI, covered by typed frontend calls, and tested before production:

## Public capabilities and catalog

```http
GET  /api/v1/public/capabilities
GET  /api/v1/services
GET  /api/v1/services/{service_id}
GET  /api/v1/services/{service_id}/questions
```

## Public forms

Preserve compatibility for current routes while defining one canonical namespace in the API registry:

```http
POST /api/v1/service-requests
POST /api/v1/contact
POST /api/v1/provider-interest
POST /api/v1/privacy-requests
POST /api/v1/communications/preferences
```

A canonical additive alias may be introduced only with compatibility tests, for example:

```http
POST /api/v2/public/submissions/service-requests
POST /api/v2/public/submissions/contact
POST /api/v2/public/submissions/provider-interest
```

Do not remove the V1 routes during this program.

## Authentication/account

```http
POST /api/v1/auth/login                 # unavailable in production when local auth is disabled
POST /api/v1/auth/register              # only if approved for the environment
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
POST /api/v1/auth/password/forgot
POST /api/v1/auth/password/reset
POST /api/v1/auth/email/verify
GET  /api/v2/me
```

## Customer

```http
GET/PATCH /api/v1/customer/profile
GET/POST  /api/v1/customer/addresses
PATCH/DELETE /api/v1/customer/addresses/{address_id}
GET /api/v1/customer/quotes
GET /api/v1/customer/quotes/{quote_id}
POST /api/v1/customer/quotes/{quote_id}/decision
GET /api/v1/customer/bookings
GET /api/v1/customer/bookings/{booking_id}
POST /api/v1/customer/bookings/{booking_id}/cancel
```

Any target-state provider, worker, operations, admin, messaging, review, payment, or payout endpoint must remain absent or capability-denied until its owning branch is implemented and approved.

# 6. Public-submission API hardening branch

Branch:

```text
be/public-submissions-hardening
```

Implement:

- typed service-request, contact, provider-interest, privacy, and communication-preference commands;
- explicit server-side consent requirement and versioned disclosure evidence;
- normalized email and E.164-compatible phone processing without losing the original permitted value;
- U.S. state/DC validation consistently across service and provider forms;
- dynamic catalog validation rather than frontend-only hardcoded service lists;
- stable idempotency with unique-constraint race handling;
- same key + same body replay;
- same key + different body conflict;
- no duplicate submission or outbox event under concurrent requests;
- rate limiting with a visible `Retry-After` contract;
- Redis failure behavior that is intentional and tested;
- honeypot plus approved abuse controls without storing the honeypot value;
- source IP hashing with documented salt/retention policy;
- payload classification and redaction;
- atomic submission + audit + outbox commit;
- downstream states that distinguish pending configuration, pending delivery, delivered, retryable failure, and terminal failure;
- dispatcher queue ownership and SLA fields;
- no appointment, provider assignment, payment, or confirmation created by public intake.

Mandatory tests:

```text
honeypot rejected
missing consent rejected
unsupported service rejected
unsupported state rejected
same idempotency request replays
changed body conflicts
concurrent duplicate creates one row/event
rate limit returns Retry-After
middleware disabled parks safely
middleware outage retries without duplicate
PII absent from logs/errors
```

# 7. Forms and CTA hardening branch

Branch:

```text
fe/public-forms-cta-hardening
```

## Refactor

Split the large `PublicIntakeForm` into reusable, tested boundaries:

```text
components/forms/PublicFormShell
components/forms/ServiceRequestForm
components/forms/ContactForm
components/forms/ProviderInterestForm
components/forms/ConsentFields
components/forms/AddressFields
components/forms/FormStatus
lib/public-submissions/client
lib/public-submissions/errors
lib/public-submissions/idempotency
content/forms/*
```

Do not duplicate state lists, service categories, consent copy, endpoint names, policy versions, or error mappings across components.

## Submission behavior

- use one stable idempotency key for retries of the exact same payload;
- generate a new key when the payload materially changes;
- retain the key after an ambiguous network/503 error;
- clear it only after an accepted result or deliberate user reset;
- display backend-safe error messages and the correlation/reference ID;
- preserve `Retry-After` and tell the user when to retry;
- distinguish catalog unavailable, capability unavailable, validation error, rate limited, temporarily unavailable, conflict, accepted, and unserviceable states;
- prevent double submit;
- keep entered data after failure;
- focus the first invalid field;
- use `aria-live`, `aria-describedby`, field-level errors, and accessible loading state;
- work at 320px through large desktop widths;
- never claim an appointment, provider, price, or payment is confirmed.

## Dynamic data

- service-request and provider-interest forms use the live service catalog;
- category labels come from the catalog/content authority;
- address validation is optional/fail-closed according to the release capability;
- provider interest may be accepted while provider self-service remains disabled;
- no fake portal or success state.

## CTA authority

Replace misleading release copy:

```text
“Book a service” → “Request a service”
“Check availability” → “Request service options” or approved request-first copy
```

The primary CTA should land on the canonical request form, not imply immediate booking.

Create one CTA registry containing:

```text
id
label
href
analytics event
allowed page families
required capability
fallback behavior
```

Validation must fail for:

- nonexistent routes;
- placeholder anchors;
- duplicate analytics IDs;
- actionless buttons;
- CTAs that require a disabled capability;
- “book/pay/confirm” language that contradicts the accepted request-first release;
- provider/admin/ops portal links before those applications are genuinely ready.

## Forms that must be production-ready now

```text
service request
contact/support
provider interest
privacy request
communication preferences
login redirect/PKCE boundary
password recovery only when supported by the identity provider
customer profile/address forms already exposed by the accepted account experience
quote decision and booking cancellation only where the backend contract already exists
```

Target-state portal forms must be built only in their owning portal branch after backend contracts are accepted.

## Analytics

Add consent-aware events without PII:

```text
cta_clicked
public_form_started
public_form_validation_failed
public_form_submitted
public_form_accepted
public_form_failed
```

Events contain route, form kind, service slug where public, capability state, and correlation ID where safe. Never send name, email, phone, address, free text, or consent disclosure text to analytics.

## Frontend tests

Require:

- component tests for all forms;
- same-payload retry reuses the idempotency key;
- changed payload receives a new key;
- error correlation is visible;
- rate-limit messaging;
- service catalog failure;
- capability disabled;
- successful reset only after acceptance;
- CTA registry integrity;
- keyboard and screen-reader behavior;
- Playwright across Chromium, Firefox, and WebKit;
- mobile/tablet/desktop responsive checks;
- serious/critical axe findings = 0 on form routes.

# 8. Durable integrations branch

Branch:

```text
integration/outbox-inbox-webhooks
```

Implement the common reliability layer before provider-specific adapters:

- claim-token-safe transactional outbox;
- expired `PROCESSING` lease recovery;
- durable integration inbox;
- provider/event uniqueness;
- signature/token/timestamp/replay verification;
- per-claim unique tokens for inbox and outbox;
- exact-token heartbeat/finalization;
- retry/backoff/terminal states;
- unknown-event terminal visibility;
- authorized manual retry/replay with separate permissions;
- operational exception creation;
- reconciliation and worker-crash tests.

# 9. Heavy marketplace branches

Each branch below is independently reviewed and capability-gated.

## Provider network

```text
be/provider-network
```

Provider organizations, memberships, workers, services, service areas, availability, credentials, insurance/licensing, suspension, eligibility, and negative cross-provider tests.

## Matching and opportunities

```text
be/matching-opportunities
```

Deterministic explainable matching, candidate reasons, no ML requirement, opportunity lifecycle, expiration, provider-specific visibility, and minimum PII disclosure.

## Quotes and conversations

```text
be/quotes-conversations
```

Versioned quotes, line items, decisions, conversation authority, attachment authorization, unread state, and no payment or automatic booking implication.

## Booking, job, and operations

```text
be/booking-job-operations
```

Manual scheduling, holds, explicit operator confirmation, assignments, job state machine, evidence, exceptions, SLA, cancellation/reschedule, and concurrency constraints.

## Private documents

```text
be/documents-private-storage
```

Private object metadata, upload sessions, signed short-lived access, type/size/checksum policy, malware scan/quarantine, cleanup, retention, and authorization.

# 10. Portal branches

## Customer portal

```text
fe/customer-portal
```

Requests, quotes, messages only when enabled, bookings, jobs, reviews only when enabled, disputes, properties/addresses, notifications, profile, auth boundary, and responsive/accessibility evidence.

## Provider and worker portals

```text
fe/provider-worker-portals
```

Provider onboarding, profile, services, areas, workers, availability, credentials, opportunities, quotes, schedule, jobs, analytics, plus worker today/jobs/schedule/availability/credentials. All routes require real backend contracts and server-side RBAC.

## Operations and admin

```text
fe/ops-admin-portals
```

Queues, matching inspection, jobs, providers, credentials, exceptions, disputes, integrations, map, analytics, users, roles, permissions, catalog, capabilities, audit, system status, and releases. No placeholder dashboards.

# 11. Provider-specific integration branch

Branch:

```text
integration/odoo-kong-n8n-klyrow-telnexa
```

This branch follows the accepted common inbox/outbox contracts and contains provider-neutral interfaces plus separately testable adapters.

Boundaries:

- BREERO PostgreSQL/PostGIS remains authoritative;
- Kong/Codestra is transport/control policy, not marketplace truth;
- Odoo 19 is CRM projection/workspace and must preserve `odoo-addons/breero_crm` plus `breero.sync.event` compatibility;
- n8n executes allowlisted workflows only and never writes BREERO tables directly;
- Klyrow transports approved email;
- Telnexa transports approved SMS;
- all external sends remain disabled until separately activated;
- every adapter has health, timeout, retry, idempotency, authentication, reconciliation, redaction, and degraded-mode tests.

# 12. Docker and release platform branch

Branch:

```text
ci/docker-release-platform
```

## Canonical topology

Select one production backend Compose authority. Reconcile:

```text
docker-compose.production.yml
deploy/production/docker-compose.backend.yml
```

Do not leave two competing definitions for the same production volumes/services.

The canonical production topology must include:

```text
frontend
API
migration one-shot job
worker
scheduler/Celery beat
PostgreSQL/PostGIS
Redis
external Caddy edge network
internal private network
```

Requirements:

- immutable image digests;
- no `latest` deployment;
- no public PostgreSQL, Redis, or FastAPI port;
- Caddy is the only public HTTP/TLS ingress;
- non-root runtime users;
- read-only filesystems;
- explicit writable tmpfs/volumes;
- `no-new-privileges` and dropped capabilities;
- resource and PID limits;
- log rotation;
- API health/readiness;
- worker and scheduler heartbeat;
- graceful shutdown;
- secret files or approved secret manager references;
- no secret value in environment examples, logs, image layers, or Git;
- `docker compose config --quiet` in CI;
- image build and HIGH/CRITICAL scan;
- SBOM and provenance;
- signed release artifacts when required;
- release manifest binding source SHA, migration head, OpenAPI digest, image digests, configuration digest, capability snapshot, checks, backup, and rollback images.

## Frontend identity

Every deployable frontend artifact must use:

```text
NEXT_PUBLIC_KEYCLOAK_ISSUER=https://auth.codestra.co/realms/codestra
```

The legacy `.agency` issuer is forbidden in deployable configuration.

# 13. Isolated staging certification

Branch:

```text
release/isolated-staging-certification
```

Deploy exact release digests to isolated staging with separate PostGIS, Redis, API, worker, scheduler, frontend, DNS/TLS, secrets, and synthetic personas.

Prove:

- migrations from clean and supported prior head;
- OpenAPI/client compatibility;
- OIDC login/logout;
- every public form end to end;
- every CTA resolves and performs the expected action;
- request intake remains request-only;
- manual operator scheduling/confirmation;
- negative payment/automatic assignment/confirmation/external-send tests;
- idempotency and concurrency;
- worker crash/lease recovery;
- adapter-disabled behavior;
- browser/accessibility/responsive matrix;
- backup and isolated restore;
- deployment rollback rehearsal.

Production is `NO_GO` if isolated staging cannot be proven.

# 14. Production deployment candidate

Branch:

```text
release/production-candidate
```

Create only from the accepted, merged, exact `main` release SHA after staging certification.

Before deployment:

- revalidate issues #17–#19 with fresh read-only host evidence;
- prove disk/capacity headroom;
- prove no public 5432/6379/8000;
- verify DNS, TLS, Caddy, networks, volumes, current database head, backup, restore, monitoring, and rollback artifacts;
- use a protected production environment and authorized reviewer;
- deploy the exact staging-certified digests;
- canary before public routing;
- roll back on health, migration, auth, CORS, worker, data, capability, or exposure failure.

Required zero-activity proof during the approved request-only deployment:

```text
PAYMENTS_ATTEMPTED=0
PAYOUTS_ATTEMPTED=0
PAID_LEAD_CHARGES=0
AUTOMATIC_ASSIGNMENTS=0
AUTOMATIC_CONFIRMATIONS=0
EMAIL_SENDS=0
SMS_SENDS=0
ODOO_WRITES=0
N8N_EXECUTIONS=0
MIDDLEWARE_DELIVERIES=0
```

# 15. Codex operating instructions

Codex must:

1. inspect current GitHub state rather than trusting the SHAs in this document;
2. stop when a dependency branch is awaiting merge/approval;
3. create only the next permitted branch;
4. implement production code, tests, migrations, contracts, and docs together;
5. open/update a draft PR;
6. never self-approve, merge, or deploy around branch protection;
7. never weaken tests to make CI green;
8. never activate a capability through route/schema/UI presence;
9. never use production as staging;
10. return an exact final report with branch, starting SHA, final SHA, commits, changed files, tests, workflow runs, review state, blockers, and next branch.

## Final status vocabulary

```text
CODE_READY=YES/NO
REVIEW_READY=YES/NO
MERGE_READY=YES/NO
STAGING_READY=YES/NO
PRODUCTION_READY=YES/NO
PRODUCTION_DEPLOYED=YES/NO
CAPABILITY_ACTIVE=YES/NO
```

These statuses are not interchangeable.
