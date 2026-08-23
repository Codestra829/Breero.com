# Marketplace V2 Integration and Deployment Readiness

Status: implementation authority for production integration and operations work  
Applies to: the existing BREERO monorepo  
Change type: documentation only; this document does not deploy, enable, or merge any feature

## 1. Architectural boundary

BREERO remains one monorepo with independently deployable surfaces:

- `apps/api`: FastAPI application and workers
- `apps/web`: public/customer Next.js 15 application
- `apps/partner`: partner Next.js 15 application
- `apps/ops`: operations Next.js 15 application
- `apps/admin`: administration Next.js 15 application
- `packages/*`: shared UI, types, API client, configuration, and utilities

Frontend and backend changes must remain separable by package ownership and PR scope. They do not require separate repositories, and the frontend must not be replaced with Vue.

The backend owns persistence, identity interpretation, authorization, business rules, state transitions, capability enforcement, idempotency, and provider integrations. Frontends consume generated typed contracts and must not recreate those rules locally.

## 2. Source-of-truth rules

- PostgreSQL/PostGIS is the source of marketplace and field-service truth.
- Redis is ephemeral infrastructure for queues, locks, throttling, and caches.
- Odoo, n8n, search indexes, email providers, SMS providers, and analytics stores are downstream projections or execution adapters.
- State changes, state history, audit records, and outbox events commit atomically.
- External callbacks never mutate business tables directly.
- Payment execution remains disabled until a separately approved payment phase enables it.
- The canonical identity issuer is `https://auth.codestra.co/realms/codestra`.
- Runtime capability discovery remains `GET /api/v2/capabilities`.

## 3. Database evolution

Use the existing tables and the current Alembic head. Do not rename or move production tables solely to create logical PostgreSQL namespaces.

A physical schema split requires its own ADR, compatibility plan, additive migrations, rollback proof, and measurement of locking and operational impact. Until then, domain ownership is expressed through application modules, repositories, migration names, and documented table ownership.

Every migration must be:

1. additive or explicitly backward compatible;
2. safe while old and new application revisions overlap;
3. tested on an empty database and an upgraded production-like database;
4. reversible where PostgreSQL can safely reverse it;
5. accompanied by a data backfill plan when needed;
6. executed once as a deployment job, never independently by every web replica.

## 4. Integration adapter contract

Provider-specific HTTP, authentication, retry, signature, and response-normalization logic lives behind adapters. Domain services depend on ports, not vendor SDKs.

Each adapter must expose only the operations required by BREERO and return BREERO-owned result and error types. At minimum it must define:

- connection validation;
- readiness evaluation;
- outbound command execution;
- inbound event verification and normalization;
- provider correlation identifiers;
- retry classification;
- safe diagnostic metadata.

Provider errors are classified as:

- `configuration_error`: missing or invalid operator configuration;
- `authentication_error`: rejected credential, certificate, or audience;
- `authorization_error`: credential lacks required provider permission;
- `rate_limited`: provider asked the caller to slow down;
- `retryable_provider_error`: timeout, transport error, or provider 5xx;
- `non_retryable_provider_error`: valid request rejected permanently;
- `invalid_signature`: inbound authenticity check failed;
- `invalid_payload`: verified callback cannot be normalized.

Do not leak provider response bodies, authorization headers, secrets, tokens, or customer documents into API responses or logs.

## 5. Provider connection registry

Add a connection registry only through an additive Alembic migration. Use the repository naming convention, for example `integration_provider_connections`, rather than inventing a new physical PostgreSQL schema.

Required fields:

- `id`;
- `provider_code`;
- nullable `tenant_id` for global versus tenant-scoped connections;
- `enabled`;
- `environment`;
- `base_url`;
- `auth_mode`;
- `secret_reference`;
- nullable `client_certificate_reference`;
- `connect_timeout_ms`;
- `read_timeout_ms`;
- `max_retries`;
- non-secret `config_json`;
- `last_validated_at`;
- `last_validation_status`;
- `created_at` and `updated_at`.

Enforce one active record per provider, environment, and scope. Store secret references, never secret values. Runtime secrets must come from the approved secret store or deployment environment.

A connection is ready only when it is enabled, its referenced material can be resolved, validation has succeeded within the allowed freshness window, and any required certificate is valid.

## 6. Durable outbound delivery

All outbound effects originate from the existing transactional outbox. A worker claims records using concurrency-safe PostgreSQL semantics, records attempts, applies bounded retries, and moves exhausted items to a visible terminal state.

Each delivery record must retain:

- event type and schema version;
- aggregate type and identifier;
- tenant identifier;
- provider and connection identifier;
- idempotency key;
- provider correlation identifier;
- attempt count and next-attempt timestamp;
- normalized error class and safe error detail;
- terminal outcome.

Business transactions must not wait for email, SMS, Odoo, n8n, analytics, or other optional providers.

## 7. Authenticated webhook inbox

Expose provider callbacks under independently versioned routes:

`POST /webhooks/v1/{provider}`

The route must:

1. read the exact raw body before JSON parsing;
2. resolve the expected provider connection;
3. verify the provider signature or mutual-TLS identity;
4. validate timestamp freshness when supported;
5. derive a stable provider event identifier;
6. insert the raw-event hash and safe metadata into a durable inbox;
7. deduplicate through a database uniqueness constraint;
8. return `202 Accepted` after the inbox commit;
9. process the event asynchronously.

Never acknowledge a callback before durable storage. Never perform slow domain work in the request path.

The inbox stores encrypted payload content only when replay requires it and retention policy allows it. Otherwise store a normalized payload plus a cryptographic body hash. It must record provider, event identifier, schema/version, received time, signature status, processing status, attempts, correlation identifiers, and safe error information.

Duplicate callbacks return the same successful acknowledgement and do not repeat business effects.

## 8. Signature verification baseline

Generic HMAC integrations require:

- an explicit signature header;
- a signed timestamp;
- constant-time comparison;
- a configured algorithm, defaulting to HMAC-SHA256;
- a narrow replay window;
- signature input built from the exact documented byte sequence;
- rotation support for current and previous secrets.

Signature verification must use the raw body. JSON reserialization is forbidden because it can change the signed bytes.

Provider-native verification takes precedence over the generic algorithm. Stripe uses its official signature construction and raw-body requirements. Codestra uses its approved mTLS, HMAC-V2, service-token, audience, tenant, and scope rules.

## 9. Provider policies

### Codestra

- Require the canonical issuer and expected audience.
- Validate tenant and required service scopes.
- Use mutual TLS and HMAC-V2 when required by the provider contract.
- Reject expired certificates and secrets.
- Preserve provider correlation identifiers in audit and delivery records.

### Odoo

- Treat Odoo as a projection, not the source of marketplace state.
- Send versioned, idempotent events from the outbox.
- Reconciliation jobs compare projected state without allowing Odoo to overwrite protected BREERO state.
- Surface backlog, repeated rejection, and reconciliation drift to operations.

### Klyrow email

- Send transactional templates only when the associated capability is enabled.
- Process delivered, bounced, complained, and suppressed callbacks through the webhook inbox.
- Apply suppression before future sends.
- Keep unrestricted marketing email disabled.

### Telnexa SMS

- Send transactional messages only when the capability and recipient policy permit them.
- Process delivery receipts and replies through the inbox.
- Respect opt-out and suppression state.
- Keep unrestricted marketing SMS disabled.

### n8n

- Trigger only allowlisted workflows with versioned event contracts.
- Sign outbound requests and require signed callbacks.
- Include tenant, aggregate, correlation, and idempotency identifiers.
- n8n receives no direct database access and cannot bypass domain commands.
- External automation remains disabled until explicitly released.

### Stripe

- Keep payment execution disabled in the current release boundary.
- It is acceptable to implement inert adapter and webhook verification foundations behind disabled capabilities.
- Do not advertise checkout, capture, refunds, paid leads, subscriptions, or payouts before the payment phase is approved.

## 10. Capability and authorization gates

A provider-dependent operation is allowed only when all of the following are true:

1. the runtime capability is enabled;
2. the authenticated principal has the required permission;
3. tenant and record-level authorization succeeds;
4. the resource is in a valid state;
5. the provider connection is ready;
6. the request passes idempotency and concurrency rules.

The backend evaluates all six conditions. Frontend visibility is an additional usability check, never authorization.

The public capability response must not expose secret references, provider credentials, internal endpoints, or sensitive validation errors.

## 11. Idempotency and concurrency

- Mutating commands that may be retried require an idempotency key.
- Scope keys by tenant, authenticated actor or public session, command, and resource as appropriate.
- Persist a request fingerprint and the first terminal response.
- Reusing a key with a different fingerprint returns a conflict.
- In-progress duplicates do not execute concurrently.
- Outbox and inbox uniqueness constraints provide final protection against duplicate provider effects.
- State transitions use optimistic version checks or explicit row locking where necessary.

## 12. Production topology on Hetzner

The supported single-host production starting point is:

`Internet -> Caddy -> Next.js surfaces and FastAPI -> PostgreSQL/PostGIS, Redis, and workers`

Only TCP 80 and 443 are public. PostgreSQL, Redis, worker management, and metrics endpoints remain on private container networks or a private interface.

Caddy terminates TLS, applies host routing, preserves request identifiers, and proxies only approved routes. A representative configuration is:

```caddyfile
api.breero.com {
    encode zstd gzip
    reverse_proxy api:8000
}

breero.com, www.breero.com {
    encode zstd gzip
    reverse_proxy web:3000
}

partner.breero.com {
    encode zstd gzip
    reverse_proxy partner:3000
}

ops.breero.com {
    encode zstd gzip
    reverse_proxy ops:3000
}

admin.breero.com {
    encode zstd gzip
    reverse_proxy admin:3000
}
```

Final hostnames must come from deployment configuration. Do not commit server IPs, credentials, private keys, or production environment files.

Container images and Python/JavaScript dependencies must be pinned to exact tested versions or immutable digests through the repository lockfiles and deployment manifest. Do not copy unverified version numbers from planning documents.

## 13. Health and readiness

Provide:

- `GET /health/live`: process is alive; no dependency calls;
- `GET /health/ready`: required dependencies are ready;
- `GET /health/dependencies`: authenticated operations-only diagnostic detail.

Readiness requires database connectivity, migration compatibility, and any infrastructure that is mandatory for the enabled release. Disabled optional providers do not fail readiness. An enabled critical provider may make the associated capability unavailable without taking the whole API offline.

Health responses must be bounded by short timeouts and must never reveal credentials, connection strings, or raw provider errors.

## 14. Timeouts, retries, and circuit breaking

Every external call has separate connect and read timeouts. Retries are allowed only for operations proven safe or protected by idempotency.

Use exponential backoff with jitter and a bounded attempt count. Honor provider retry guidance. Do not retry permanent authentication, authorization, validation, or business-rule failures.

Repeated provider failure opens a circuit or marks the connection unavailable. Recovery uses a bounded probe. Capability evaluation reflects provider readiness without causing a network call on every request.

## 15. Structured logs and metrics

Emit structured logs with:

- timestamp and severity;
- service and deployment revision;
- request or job correlation identifier;
- tenant identifier when safe;
- authenticated subject identifier when safe;
- route or worker name;
- aggregate type and identifier;
- provider and normalized outcome;
- latency and retry attempt;
- normalized error class.

Redact authorization headers, cookies, tokens, secret references where sensitive, full webhook payloads, customer documents, and unnecessary personal data.

Minimum metrics:

- HTTP request count, latency, and error rate;
- database pool use and query latency;
- queue depth and job age;
- outbox backlog, attempts, and terminal failures;
- webhook receipt, signature rejection, duplicate, processing age, and failure counts;
- provider request latency, status class, retry, circuit, and readiness;
- capability-denied operations by safe reason;
- deployment and migration revision.

Alerts must focus on user impact and durable backlog age, not raw log volume.

## 16. Backup and restore

Back up PostgreSQL with encryption, retention, and off-host storage. Backups are incomplete until restore is tested.

The runbook must document:

- backup schedule and retention tiers;
- encryption and key ownership;
- off-host destination;
- integrity checks;
- restore to an isolated environment;
- migration compatibility after restore;
- target recovery point and recovery time;
- quarterly restore-drill evidence;
- operator escalation.

Redis is not the sole store of durable business data and does not substitute for PostgreSQL backups. Uploaded documents require an independent object-storage backup and retention policy.

## 17. Deployment sequence

1. Build reproducible images and record their digests.
2. Run lint, typecheck, unit, integration, migration, security, and E2E checks.
3. Back up the database and confirm backup health.
4. Run the migration job once.
5. Deploy API and worker revisions compatible with the old and new schema.
6. Deploy frontend surfaces using the matching generated client.
7. Verify liveness, readiness, migration revision, queue workers, and capabilities.
8. Run smoke tests for zero-provider and configured-provider cases.
9. Observe error rate, latency, inbox/outbox age, and provider health.
10. Roll back application revisions independently; apply a database rollback only when its safety is proven.

Use rolling or blue/green deployment where practical. Never rely on manual database edits as a release step.

## 18. Delivery ownership

This authority extends the existing sequential plan; it does not create a permanent integration mega-branch.

Suggested focused backend PRs after the P0 production foundation:

- `be/marketplace-v2-integrations`: provider ports, registry, outbox consumers, and inert adapters;
- `be/marketplace-v2-webhook-inbox`: verified callback intake, deduplication, and async processing;
- `be/marketplace-v2-observability`: logs, metrics, alerts, and operations diagnostics;
- `be/marketplace-v2-hetzner-deployment`: production manifests, Caddy, migration job, backups, and rollback runbook.

Frontend PRs consume the generated OpenAPI client and the canonical capability endpoint. They do not contain provider credentials or reproduce readiness rules.

## 19. Required tests

At minimum, prove:

- a disabled provider cannot be invoked;
- a capability cannot bypass permission or record authorization;
- an expired secret or certificate makes the provider unavailable;
- a webhook with an invalid signature produces no inbox or business effect;
- a replayed webhook is acknowledged once and processed once;
- an outbox retry produces one provider-side effect;
- provider timeout and rate-limit behavior is bounded;
- a connection for one tenant cannot serve another;
- n8n cannot mutate the database directly;
- Odoo reconciliation cannot overwrite protected state;
- optional-provider failure does not fail core API readiness;
- logs and diagnostic responses contain no secret;
- a clean install and production-like upgrade reach the same schema;
- backup restore succeeds in an isolated environment;
- rollback preserves the payment-free marketplace lifecycle.

## 20. Definition of done

Integration and deployment readiness is complete only when:

- adapters isolate provider-specific code;
- connection data contains references rather than secrets;
- webhook authenticity and replay protection are tested;
- inbox and outbox processing are durable and observable;
- provider readiness participates in backend capability enforcement;
- the Hetzner deployment exposes only approved public ports;
- dependency versions and images are reproducibly pinned;
- health checks, timeouts, retries, and circuits are bounded;
- backups have current restore-drill evidence;
- migrations and rollback are documented and tested;
- the canonical zero-provider path remains fully functional;
- disabled payments, marketing, and external automation remain impossible to execute or advertise.
