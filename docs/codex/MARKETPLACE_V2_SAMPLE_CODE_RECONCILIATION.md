# Marketplace V2 Sample-Code Intake and Reconciliation

Status: authoritative disposition of the standalone FastAPI/Vue sample  
Applies to: implementation work in the existing BREERO monorepo  
Change type: documentation only; no sample source file is approved as production code

## 1. Decision

Do not copy the attached standalone `breero-backend` or `breero-frontend` trees into the repository.

The sample is useful as implementation intent, but it is not a production-ready implementation. It conflicts with BREERO's established architecture and contains security, consistency, and reliability defects that must not enter an implementation branch.

BREERO remains:

- a FastAPI backend in `apps/api`;
- Next.js 15 applications in `apps/web`, `apps/partner`, `apps/ops`, and `apps/admin`;
- shared generated contracts and UI in `packages/*`;
- one PostgreSQL/PostGIS source of truth;
- additive Alembic migrations from the actual head at branch creation time;
- payment-free and manual-dispatch-first until explicit release gates approve otherwise.

This document supplements, and does not replace:

- `MARKETPLACE_V2_P0_PRODUCTION_FOUNDATION.md`;
- `MARKETPLACE_V2_BACKEND_IMPLEMENTATION_AUTHORITY.md`;
- `MARKETPLACE_V2_FRONTEND_BACKEND_PR_TRACKS.md`;
- `MARKETPLACE_V2_INTEGRATION_DEPLOYMENT_READINESS.md`;
- `MARKETPLACE_V2_ACCEPTANCE_TESTS.md`.

## 2. What may be retained as intent

The implementation may retain these concepts after adapting them to the existing codebase:

- environment-backed settings with safe disabled defaults;
- issuer-plus-subject external identity binding;
- server-owned runtime capabilities;
- command idempotency with request fingerprints;
- explicit ProjectRequest, Opportunity, LeadConnection, Quote, Conversation, Message, Job, and Review aggregates;
- transactional outbox and authenticated inbox;
- concurrency-safe worker claiming;
- provider adapters with bounded HTTP timeouts;
- structured request correlation;
- liveness and readiness endpoints;
- private database and Redis networks behind Caddy;
- a generated typed frontend client;
- UI capability gates as usability controls.

Concept approval does not approve the sample implementation.


## 2.1 Mandatory production-correction checklist

Before any implementation derived from the sample may be described as production-ready, it must:

1. replace deterministic JWT `uuid5()` identity generation with the `external_identities` database mapping;
2. cache OIDC discovery and JWKS safely while supporting signing-key rotation;
3. use one coherent browser/API authentication flow instead of the sample frontend/backend bearer-token mismatch;
4. move business logic out of route files and into domain/application services;
5. return explicit response DTOs instead of ORM entities;
6. enforce participant and tenant authorization on message creation;
7. derive quote provider identity from the authenticated provider membership rather than accepting an arbitrary `provider_id`;
8. add immutable quote versions and quote line items;
9. add immutable job status and assignment history;
10. make idempotency acquisition and replay safe under concurrent requests;
11. make outbox leases reclaimable and fence stale workers;
12. add persisted `delivered_at`, normalized `last_error`, and delivery-attempt evidence to the outbox schema;
13. cryptographically verify every webhook before accepting it as trusted;
14. process verified inbox records asynchronously instead of running third-party business work inline;
15. implement PostGIS eligibility and distance matching with reproducible reasons;
16. add database uniqueness constraints for marketplace relationships and treat them as final duplicate protection;
17. use timezone-aware UTC timestamps everywhere and preserve required local timezone context;
18. wrap every state transition, history entry, audit record, outbox event, and idempotency result in one transaction;
19. generate the shared TypeScript API client from canonical OpenAPI for the existing Next.js applications;
20. complete additive migrations plus concurrency, integration, authorization, security, browser, and accessibility tests.

These requirements align with the unfinished work already recorded by the V2 architecture and are mandatory implementation gates, not optional cleanup.

## 2.2 Core production rule

```text
FRONTEND
= display + interaction

BACKEND
= identity + permissions + business rules + state

DATABASE
= authoritative state

WORKERS
= asynchronous and retryable work

OUTBOX / INBOX
= reliable integration boundary
```

No frontend, provider, workflow engine, cache, or third-party callback may bypass this boundary.

## 3. Canonical landing map

| Sample location | BREERO implementation location |
|---|---|
| standalone `app/config.py` | existing API settings/configuration modules |
| single `app/db/models.py` | domain-owned SQLAlchemy model modules |
| standalone `migrations/` | existing Alembic environment and actual current head |
| route-local business logic | router → service → repository/query → async SQLAlchemy |
| `app/core/auth.py` | existing Keycloak/OIDC authentication and identity-binding modules |
| `app/core/capabilities.py` | server-owned capability service and canonical endpoint |
| `app/core/idempotency.py` | transaction-safe command/idempotency service |
| `app/integrations/*` | existing integration ports, provider adapters, outbox/inbox workers |
| standalone worker loop | existing worker runtime with leases, metrics, shutdown, and recovery |
| standalone Vue frontend | existing Next.js surfaces and shared generated client |
| replacement Compose/Caddy files | existing deployment manifests, overlays, and runbooks |

No implementation PR may introduce a second source of truth or bypass the existing application layering.

## 4. Critical defects that must not be copied

### 4.1 Unauthorized message creation

The sample checks conversation participation on message reads but does not repeat or reuse that authorization on message creation. Any authenticated user who discovers a conversation identifier could attempt a cross-tenant write.

Required correction:

- authorize membership in the service layer for every read and write;
- scope by tenant and conversation participant;
- use a non-disclosing not-found response where policy requires it;
- test customer, provider, worker, operations, former-member, and cross-tenant negatives.

### 4.2 Quote creation trusts caller-supplied provider identity

The sample accepts `provider_id` from the request body and creates a quote without proving provider membership, permission, LeadConnection access, request state, or tenant ownership.

Required correction:

- derive provider organization from the authenticated membership and route context;
- require quote permission and an active authorized marketplace connection;
- create immutable quote versions and line items;
- use idempotency, state history, audit, and outbox in one transaction.

### 4.3 Quote acceptance bypasses the release boundary

The sample changes a ProjectRequest directly to `BOOKED` when a quote is accepted. It creates no Booking aggregate and does not evaluate booking, payment, provider-readiness, or confirmation policy.

Required correction:

- quote acceptance is its own domain command;
- persist the accepted quote decision atomically;
- create a booking only through the approved downstream booking policy;
- never confirm a booking or execute payment while those capabilities are disabled;
- preserve the current request-only/manual-dispatch behavior until its gate is approved.

### 4.4 Webhook verification is fictitious

The sample parses the body and stores `signature_verified=True` while explicitly omitting authentication. This is not a placeholder that may be deployed.

Required correction:

- route callbacks through `POST /webhooks/v1/{provider}`;
- verify raw bytes before parsing;
- require provider-native signature or mTLS validation;
- enforce timestamp freshness and replay protection;
- resolve the provider connection and tenant safely;
- insert into the durable inbox only after successful verification;
- reject invalid callbacks without any business effect.

### 4.5 Idempotency acquisition races

The sample performs a read followed by an insert. Two concurrent requests can both observe no record and race at flush. It also does not define safe behavior for an existing `IN_PROGRESS` record.

Required correction:

- use an atomic insert/upsert or handle the uniqueness conflict within a savepoint;
- scope by tenant, actor/session, command, and resource;
- persist a canonical request fingerprint;
- return the stored terminal status, headers, and body for a valid replay;
- return conflict for key reuse with different content;
- return a defined retryable response for an in-progress command;
- recover abandoned in-progress records through explicit policy;
- cover simultaneous first use with a real PostgreSQL concurrency test.

### 4.6 Job commands lack assignment and permission checks

The sample proves only that the actor belongs to the provider. It does not prove worker assignment, role permission, tenant scope, evidence requirements, or command-specific eligibility.

Required correction:

- centralize transitions in the Job domain service;
- verify provider, worker, assignment, permission, state, and capability;
- validate required notes, diagnostics, evidence, and approval before completion;
- persist job history, audit, and outbox atomically;
- require idempotency on every transition.

### 4.7 External identity binding is temporary and unsafe as authority

The deterministic UUID derived from issuer and subject is explicitly temporary. It bypasses lifecycle handling for linked, merged, disabled, or migrated identities.

Required correction:

- require the canonical issuer `https://auth.codestra.co/realms/codestra`;
- validate issuer, audience, signature, expiry, not-before, token type, and required claims;
- bind `issuer + subject` through the external identity table;
- link that record to an internal user under a controlled transaction;
- do not use email as identity;
- reject conflicting identity links and disabled users;
- record safe authentication and authorization audit evidence.

### 4.8 JWKS retrieval is unsuitable for request-time production use

The sample downloads discovery metadata and JWKS for each request. It has no bounded cache, key-rotation strategy, stale-key policy, or protection against dependency storms.

Required correction:

- cache discovery and keys with bounded freshness;
- refresh safely on an unknown key identifier;
- tolerate rotation without accepting untrusted algorithms;
- fail closed when verification cannot be established;
- expose safe metrics without logging tokens.

### 4.9 Outbox leasing is incomplete

The sample writes lease fields but does not select expired leases, verify lease ownership during completion, or protect against a prior worker finalizing after another worker reclaims the record. It references delivery state not present in the shown model and uses unclassified retries without jitter.

Required correction:

- claim pending and expired-leased records atomically;
- assign a unique lease token, owner, and deadline;
- update completion only when the lease token still matches;
- use heartbeat/renewal only for bounded long-running work;
- classify retryable versus terminal errors;
- use exponential backoff with jitter and provider guidance;
- persist delivery attempt history and provider correlation identifiers;
- expose backlog age, lease recovery, retry, and terminal-failure metrics;
- implement graceful shutdown without losing claimed work.

### 4.10 Transactional history and audit are missing

Several sample commands commit only the current aggregate. They omit state history, audit, and outbox; some create endpoints commit without idempotency.

Required correction:

`aggregate state + version + immutable history + audit + outbox + idempotency terminal result`

must commit in one database transaction for every state-changing command.

### 4.11 ORM entities are returned directly

The sample returns SQLAlchemy objects from public and authenticated routes. This can expose fields unintentionally and makes contract evolution depend on persistence layout.

Required correction:

- define explicit Pydantic input and output schemas;
- use response models for every route;
- expose only approved projections;
- keep public provider data separate from internal provider data;
- use stable operation identifiers and regenerate OpenAPI.

### 4.12 Capability logic is incomplete

The sample uses environment booleans only and publishes them under a conflicting `/api/v2/public/capabilities` path.

Required correction:

- preserve `GET /api/v2/capabilities`;
- calculate effective capability from release configuration, tenant entitlement, principal permission, record authorization, resource state, and provider readiness;
- never rely on frontend visibility;
- keep payments, payouts, paid leads, automatic assignment, automatic confirmation, marketing, unrestricted email/SMS, and external automation disabled.

## 5. High-risk incompleteness

The following sample behavior must be redesigned before implementation:

- public provider queries have no cursor pagination or explicit response projection;
- provider membership selection is ambiguous for users with multiple organizations;
- opportunity expiry is mutated and then followed by an exception, which rolls the mutation back;
- opportunity acceptance lacks history, audit, outbox, permission, and disclosure-policy enforcement;
- LeadConnection uniqueness and active-connection policy are underspecified;
- quote versions and quote line items are absent;
- conversation participants and read cursors are absent;
- message delivery, attachment authorization, moderation, and rate limits are absent;
- job state omits diagnosing, approval, evidence, cancellation, and history requirements;
- review insertion depends on a pre-read rather than treating the unique constraint as final concurrency protection;
- review moderation, dimensions, response, and verified-review projection are absent;
- provider service areas, credentials, workers, availability, matching explanations, and holds are absent;
- webhook payload retention and encryption policy are absent;
- provider connection registry and secret references are absent;
- API errors are inconsistent and not the canonical problem-detail contract;
- create endpoints lack idempotency and transactional event publication;
- datetime usage mixes naive and timezone-aware values;
- monetary database values and API projections are not fully validated;
- health readiness checks only the database and has no timeout or migration-compatibility proof.

## 6. Frontend disposition

The Vue files must not be added. Reimplement approved behavior in the existing Next.js applications.

The sample frontend has additional defects:

- its handwritten types can drift from OpenAPI;
- it calls the noncanonical capabilities path;
- it uses cookie credentials while the shown backend expects bearer authentication;
- it generates a new idempotency key inside the submit action, so an uncertain retry can create a new command;
- it exposes raw service, address, and job identifiers as end-user inputs;
- it offers job controls without authenticated route and record policy;
- capability load failure is treated as loaded-but-disabled without a distinct degraded state;
- it lacks complete loading, empty, error, conflict, session-expiry, and offline recovery;
- it lacks the customer, partner, worker, operations, and administration route boundaries;
- it provides no evidence for accessibility, responsive behavior, browser tests, or generated-client compatibility.

Required frontend pattern:

1. generate the shared TypeScript client from the merged backend OpenAPI;
2. place authenticated transport and normalized errors in the shared API-client package;
3. create an idempotency key once per user intent and retain it across uncertain retries;
4. use the canonical capability response for visibility and explanation;
5. keep backend authorization authoritative;
6. build each surface only after its backend contract merges;
7. test negative authorization and capability behavior through the browser.

## 7. API corrections

Use the canonical routes defined by the V2 API authority. In particular:

- capabilities: `GET /api/v2/capabilities`;
- public providers: `GET /api/v2/providers` and `GET /api/v2/providers/{slug}`;
- partner opportunities: `/api/v2/partner/opportunities/*`;
- partner quote creation and sending: `/api/v2/partner/project-requests/{id}/quotes` and quote commands;
- customer quote decisions: `/api/v2/quotes/{id}/accept` and `/decline`;
- verified reviews: `POST /api/v2/jobs/{id}/reviews`;
- provider callbacks: `POST /webhooks/v1/{provider}`.

No generic status PATCH is permitted.

## 8. Model corrections

Do not consolidate the complete schema into one new model file. Implement domain-owned tables from the data authority with:

- UUID primary keys and tenant keys where applicable;
- explicit foreign keys and deletion policies;
- enums or validated constrained state values;
- money in integer minor units and ISO currency;
- UTC timestamps plus required local timezone metadata;
- optimistic aggregate versions;
- immutable status history;
- quote and message versioning where required;
- database uniqueness as final duplicate protection;
- check constraints for rating, money, time, capacity, and status invariants;
- GiST indexes for geography;
- partial and composite indexes for operational queues;
- relationships that do not create unsafe implicit cascades.

Migration identifiers and table names are selected only after inspecting the implementation branch's current models and Alembic head.

## 9. Integration corrections

The sample static middleware bearer token is not the production machine-auth design.

Codestra communication must implement the approved combination of:

- short-lived client-credentials tokens with the correct audience and scopes;
- canonical issuer validation;
- mutual TLS where required;
- HMAC-V2 request signing where required;
- tenant, event, correlation, and idempotency identifiers;
- credential rotation through secret references;
- bounded timeouts, retries, and circuit state.

Klyrow, Telnexa, Odoo, n8n, and Stripe each require their own adapter and webhook verifier. Stripe remains inert while payments are disabled. n8n receives no direct database access. Odoo remains a projection.

## 10. Deployment corrections

Do not replace existing deployment files with the sample Compose and Caddy configuration.

Before changing deployment:

- inspect current service names, networks, volumes, images, commands, health checks, and secret paths;
- pin images to exact tested versions or immutable digests;
- use the approved secret store or runtime secret injection;
- keep PostgreSQL, Redis, workers, and metrics private;
- expose only TCP 80 and 443 publicly;
- run Alembic once as a deployment job;
- include backup, restore, rollback, resource-limit, shutdown, and observability configuration;
- ensure Caddy routing covers all actual Next.js surfaces and FastAPI;
- validate TLS, forwarded headers, trusted proxies, body limits, timeouts, and WebSocket behavior;
- do not commit production addresses, credentials, certificates, or environment files.

## 11. Evidence handling

The sample's statements about test counts, dependency versions, migration head, or green status are not release evidence.

Every implementation PR must record fresh evidence from its exact head SHA:

- current Alembic head and upgrade path;
- lint and formatting;
- Python and TypeScript type checking;
- unit tests;
- PostgreSQL/PostGIS integration tests;
- authorization and cross-tenant negative tests;
- idempotency and concurrency tests;
- inbox/outbox retry and lease-recovery tests;
- generated OpenAPI/client drift check;
- browser and accessibility tests for affected flows;
- container build and vulnerability checks;
- migration rollback or documented forward-fix strategy;
- final diff and rollback instructions.

A planning document, code excerpt, local result from a different SHA, or stale test count cannot make an API green.

## 12. Implementation sequence

Do not implement the attachment as one commit.

1. Complete and merge the six P0 production-foundation PRs.
2. Create domain schema and migrations from the latest merged target.
3. Implement ProjectRequest through service and repository layers.
4. Implement provider tenancy, credential, service-area, and availability authority.
5. Implement matching, Opportunity, and LeadConnection with controlled disclosure.
6. Implement conversations and quotes with immutable versions.
7. Implement Booking and Job only behind the release boundary.
8. Implement verified reviews from completed eligible jobs.
9. Implement provider registry, outbox delivery, authenticated inbox, and adapters.
10. Regenerate OpenAPI and merge the shared Next.js client.
11. Implement frontend surfaces in their canonical applications.
12. Add observability and Hetzner deployment changes through focused PRs.
13. Run the complete acceptance suite and controlled release process.

Each branch starts from the latest merged predecessor and stays within its assigned scope.

## 13. Definition of done for this intake

This sample-code intake is correctly handled when:

- no standalone backend repository is introduced;
- no Vue rewrite is introduced;
- no insecure placeholder is copied;
- every retained concept is implemented through existing BREERO modules;
- all canonical paths and release gates are preserved;
- all database changes use inspected additive migrations;
- auth, authorization, capability, idempotency, state, audit, and outbox rules are enforced together;
- signed webhook and worker-leasing behavior has executable evidence;
- frontend contracts come from generated OpenAPI;
- fresh CI evidence belongs to the exact implementation SHA;
- no one describes the sample or this documentation commit as production-green.
