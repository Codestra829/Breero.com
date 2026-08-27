# BREERO Ultimate Master Execution Map

Status: **binding branch and acceptance authority**

Source authority: `BREERO ULTIMATE MASTER FEATURES + SOFTWARE INSTALLATION + INFRASTRUCTURE MISSION` supplied on 2026-08-27.

This document maps that mission onto the current BREERO repository. It does not silently replace the repository's supported architecture, imply that unimplemented domains are complete, or activate protected production behavior.

## 1. Mission outcome

BREERO must become one coherent production-grade home-services marketplace supporting:

```text
PUBLIC WEBSITE
CUSTOMER MARKETPLACE
BOOKING AND QUOTE ENGINE
CLIENT ACCOUNTS
SERVICE PROVIDER NETWORK
PROVIDER CAPACITY
PROVIDER MATCHING
MANUAL DISPATCH
ADMINISTRATION
TRUST AND COMPLIANCE
REVIEWS
LEAD MANAGEMENT
COMMUNICATION
ANALYTICS
SECURITY
OBSERVABILITY
DEPLOYMENT
```

Landing pages, forms, dashboards, mock APIs, and demo authentication are not a completed marketplace.

## 2. Existing architecture audit

The repository already uses a supported modular-monolith architecture:

```text
BACKEND=FastAPI + Python 3.12
ORM=SQLAlchemy async
MIGRATIONS=Alembic
DATABASE=PostgreSQL 17 + PostGIS
CACHE_AND_QUEUE=Redis + Celery
FRONTEND=Next.js 15 + React 19 + TypeScript
PACKAGE_MANAGER=pnpm 10 + Turborepo
IDENTITY=Keycloak/OIDC with local non-production compatibility paths
CONTAINERS=Docker + Docker Compose
EDGE=Caddy/Kong boundaries
CI=GitHub Actions
TESTING=pytest, Vitest, Testing Library, Playwright Chromium/Firefox/WebKit
```

The source mission instructs the implementation agent to extend a supported existing architecture instead of replacing it. Therefore:

```text
ASP.NET_CORE_REWRITE=NOT_APPLICABLE
ENTITY_FRAMEWORK_REWRITE=NOT_APPLICABLE
AZURE_ONLY_REWRITE=NOT_APPLICABLE
FASTAPI_NEXT_POSTGRES_ARCHITECTURE=PRESERVED
```

Azure services and Bicep remain optional future infrastructure choices, not a prerequisite for implementing marketplace domains in the current Docker/GitHub deployment model.

## 3. Runtime and dependency policy

Before changing a runtime or package:

```text
classify REQUIRED / OPTIONAL / FUTURE / ALREADY_INSTALLED / NOT_APPLICABLE
check existing equivalent
check framework compatibility
check security and support status
check license and maintenance
prefer native framework capability
update lockfiles
run the complete exact-head gate
```

Node 24 certification is a separate runtime branch. It must not be mixed into provider, booking, dispatch, portal, or payment features.

## 4. Protected production posture

Until separately implemented, reviewed, staged, approved, and activated:

```text
AUTO_ASSIGN_PROVIDER=false
AUTO_CONFIRM_BOOKING=false
PAYMENTS_ENABLED=false
LIVE_PROVIDER_DISPATCH=false
LIVE_EMAIL_DELIVERY=false
LIVE_SMS_DELIVERY=false
LIVE_CALLBACKS=false
ODOO_DELIVERY_ENABLED=false
ODOO_WRITE_ENABLED=false
PROVIDER_ASSIGNMENT_MODE=MANUAL
MESSAGING_ENABLED=false
REVIEWS_ENABLED=false
FEATURED_PROVIDERS_ENABLED=false
LEAD_BILLING_ENABLED=false
```

The system may implement interfaces and disabled code paths without activating them.

## 5. Dependency-ordered branch program

Every branch opens as a draft PR, owns one heavy responsibility, preserves accepted compatibility, reports exact starting/final SHAs, and cannot deploy merely because CI is green.

### Phase A — governance, design, runtime, API foundation

```text
ci/required-check-governance
fe/enterprise-design-governance
chore/node24-runtime-certification
be/marketplace-v2-p0-api-foundation
be/api-contract-cleanup
be/auth-identity-tenancy-rbac
```

Acceptance:

- unambiguous required `quality` aggregator;
- shared enterprise and marketplace experience system;
- runtime upgrade proven separately;
- stable error, trace, pagination, OpenAPI, idempotency and concurrency conventions;
- immutable external identity mapping;
- deny-by-default tenant, permission and record policy;
- local production authentication disabled.

### Phase B — service catalog, address, geography, timezone, hours

Branch:

```text
be/catalog-geography-timezone-hours
```

Owns:

```text
categories
subcategories
services
service slugs and descriptions
duration and buffers
pricing modes
required skills/licenses/compliance
address-provider abstraction
normalization and validation
ZIP and ZIP+4
city/state/county
coordinates
IANA timezone resolution
DST handling
BREERO service zones
operating hours
Sunday emergency policy
geospatial indexes and queries
```

Mandatory tests include spring-forward, fall-back, ambiguous/non-existent local times, Arizona, Hawaii, service-zone precedence, unsupported ZIP, address-provider failure, and PostGIS coverage behavior.

### Phase C — provider network, teams, service areas, compliance, documents

Branches:

```text
be/provider-network-teams
be/provider-coverage-schedule
be/provider-compliance-documents
```

`be/provider-network-teams` owns organization registration, team membership, provider administrators, professionals/workers, services, skills, status and tenancy.

`be/provider-coverage-schedule` owns ZIP/city/county/zone/radius coverage, weekly availability, exceptions, vacation, sick time, training, manual blocks, holidays, emergency schedule and temporary overrides.

`be/provider-compliance-documents` owns identity/business/license/insurance/background/service-qualification status, expiration, secure private object storage, upload sessions, malware/quarantine policy, verification, suspension and eligibility exclusion.

Provider registration never equals approval. A provider cannot extend BREERO's outer service boundary.

### Phase D — capacity, travel and atomic holds

Branch:

```text
be/scheduling-capacity-holds
```

Owns:

```text
service duration
before/after buffer
travel-estimation abstraction
existing bookings
active holds
manual blocks
time off
daily job and work-minute limits
maximum concurrent jobs
emergency reserves
job capacity
time capacity
30-minute HELD/CONVERTED/EXPIRED/RELEASED lifecycle
atomic reservation
```

Mandatory concurrency proof:

```text
Customer A and Customer B request the same final capacity simultaneously.
Only allowed capacity survives.
```

### Phase E — requests, quotes, bookings, rescheduling, cancellation, change orders

Branches:

```text
be/request-quote-lifecycle
be/booking-reschedule-cancel
be/change-orders
```

`be/request-quote-lifecycle` preserves `INSTANT_BOOKABLE`, `QUOTE_REQUIRED`, and `REQUEST_ONLY`, versioned quotes and line items, customer decisions, communication ownership and conversion rules.

`be/booking-reschedule-cancel` owns booking creation, hold conversion/release, service-address timezone, history, cancellation/rescheduling policy, optimistic concurrency and idempotency.

`be/change-orders` owns proposed additional work, customer accept/reject, immutable agreed-scope history and effective pricing updates.

No branch silently changes agreed scope or creates payment state.

### Phase F — matching, candidate scoring and manual dispatch

Branches:

```text
be/provider-matching-scoring
be/manual-dispatch-assignment
fe/dispatch-console
```

Eligibility filters before scoring:

```text
provider/professional active
provider approved
compliance valid
service and skill qualified
coverage matched
schedule matched
no time-off or conflict
capacity available
Sunday/emergency eligible
```

Configurable internal score inputs:

```text
availability
distance
exact skill
remaining capacity
reliability
eligible customer rating
acceptance history
```

Internal scores are not exposed publicly. Current assignment mode remains manual. Candidate ranking may advise dispatch but cannot auto-assign until separately activated.

### Phase G — customer, provider, worker and internal portals

Branches:

```text
fe/customer-marketplace-portal
fe/provider-organization-portal
fe/worker-field-service-portal
fe/operations-support-trust-portals
fe/admin-platform-portal
```

Each portal is backed by real APIs, authorization, persistence and complete data states. No portal uses fabricated KPIs, counts, providers, payments, reviews, messages or success data.

The shared `@breero/ui` marketplace system controls service cards, pricing modes, trust evidence, capacity signals, lifecycle timelines and loading/empty/error/restricted/disabled/success states.

### Phase H — messaging, notifications and support cases

Branches:

```text
be/messaging-conversations
be/notifications-templates
be/support-cases
fe/messaging-support-experience
```

Messaging requires authorized booking/customer/provider/support relationships, attachment policy, read/unread, timestamps, audit and privacy.

Notifications support in-app, email, SMS and future push through versioned event/channel/language templates. Live email/SMS remain disabled until separate provider and activation gates.

Support cases keep public messages separate from internal notes and authorize attachments independently.

### Phase I — reviews, trust moderation and provider performance

Branches:

```text
be/reviews-moderation
be/provider-performance
fe/reviews-trust-experience
```

Only customers with eligible completed service may create verified-job reviews. Support provider response, moderation, reporting and publication state.

Provider performance includes completion, cancellation, decline, reassignment, on-time, acceptance, completion rate, eligible rating/count, response time and complaint rate. Internal risk scores remain private.

### Phase J — leads and commercial placement

Branches:

```text
be/lead-management
be/featured-provider-infrastructure
fe/leads-commercial-admin
```

Lead and booking concepts remain distinct.

Lead management owns source, qualification, category, geography, distribution, claim, acceptance/rejection, expiration, status, outcome and disabled billing state.

Featured/sponsored placement owns campaign, category/ZIP sponsorship, budget, dates, impressions, clicks, leads and conversions. Commercial placement never overrides service qualification, coverage, licensing, compliance, schedule, capacity or safety.

### Phase K — payments infrastructure, disabled by default

Branches:

```text
be/payments-refunds-infrastructure
be/provider-earnings-payouts
fe/finance-payment-experience
```

Do not begin before identity, authorization, audit, idempotency, concurrency, booking, quote, outbox/inbox, reconciliation and finance separation-of-duty foundations pass.

Never store raw card numbers. Use a PCI-compliant provider and sandbox during implementation.

```text
PAYMENTS_ENABLED=false
PAYOUTS_ENABLED=false
```

### Phase L — analytics, observability, privacy, retention and exports

Branches:

```text
be/analytics-observability
be/privacy-retention-exports
fe/analytics-system-health
```

Own structured logs, traces, metrics, health, queue/lease age, booking/request/capacity/provider metrics, PII redaction, classifications, configurable retention, audited asynchronous exports, dashboards and runbooks.

### Phase M — integrations and durable delivery

Branches:

```text
integration/outbox-inbox-webhooks
integration/odoo-projection
integration/n8n-orchestration
integration/klyrow-email
integration/telnexa-sms
```

All external mutation goes through authenticated commands, transactional outbox, durable signed inbox, replay protection, idempotent translators, retries, circuit/degraded behavior, dead-letter visibility and reconciliation.

Odoo is a projection/workspace rather than authoritative marketplace state. n8n orchestrates; it does not own correctness.

### Phase N — local development, CI, staging and production release

Branches:

```text
chore/local-development-bootstrap
ci/security-performance-matrix
ci/docker-release-platform
infra/production-topology
release/isolated-staging-certification
release/production-candidate
```

Own:

```text
clone/configure/install/start/migrate/seed/run scripts
safe local demo data
safe email/SMS adapters
frozen dependency installs
lint/type/build/unit/integration/database/E2E/OpenAPI/migration/security tests
performance smoke
immutable digest-pinned images
SBOM/provenance/signing policy
one canonical production Compose topology
private PostgreSQL/Redis/application networks
Caddy/Kong ingress
backup and isolated restore
rollback rehearsal
staging UAT
production canary and abort thresholds
```

Production is never the first environment receiving a migration.

## 6. Design acceptance

The binding design authorities are:

```text
docs/design-system.md
docs/marketplace-experience-system.md
docs/design-system-migration.md
```

New or materially edited pages must support:

```text
search
filter
sort
pagination where applicable
forms and backend validation
drawers/dialogs and focus recovery
loading
empty
error
restricted
disabled
success
mobile widths 320 through 1440+
keyboard and screen-reader behavior
reduced motion
Chromium/Firefox/WebKit
```

The interface must distinguish request, quote, booking, assignment, job and completion states.

## 7. API acceptance

Every API operation documents:

```text
owner
audience
authentication
role and permission
tenant and legal entity
ownership and record policy
resource state
feature/capability
idempotency
concurrency/version
request and response
errors and headers
rate limits
emitted events
deprecation
```

An endpoint is not complete merely because it exists. Authorization, persistence, concurrency, migrations and failure behavior must be tested.

## 8. Complete test matrix

Each applicable branch contributes to:

```text
unit
integration
PostgreSQL/PostGIS
API contract
authentication and authorization
ownership and provider tenancy
booking and quote state
ZIP/service zone/timezone/DST
hours and Sunday emergency
provider matching and capacity
30-minute holds and double-booking protection
cancellation/rescheduling/assignment/reassignment
compliance and secure files
reviews and moderation
rate limiting and abuse
accessibility and responsive behavior
E2E
migration and rollback
security
performance smoke
backup and restore
```

## 9. Final completion rule

Nothing is complete merely because it renders.

Nothing is complete merely because an endpoint exists.

Nothing is complete unless:

```text
authorization is tested
data persists
concurrency is safe
migrations work
rollback or forward-fix is evaluated
required tests pass
exact-head CI passes
fresh review applies to the final SHA
staging evidence exists for release work
protected production features remain controlled
```

## 10. Current authority state

```text
CURRENT_MAIN_SHA=35beb55eedb3f58eb39caf40ffaa9795978d6ee7
DESIGN_AUTHORITY_PR=67
DASHBOARD_INTERACTIONS_PR=69
IDENTITY_RBAC_PR=68
PLANNING_AUTHORITY_PR=47
PRODUCTION_DEPLOYED=NO
LIVE_SERVER_CHANGED=NO
ULTIMATE_MISSION_COMPLETE=NO
```

This document defines execution; it does not falsely mark the full marketplace complete.
