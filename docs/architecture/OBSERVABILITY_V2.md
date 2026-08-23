# BREERO Marketplace V2 Observability

## Correlation

Generate or accept a correlation ID at ingress and carry it through domain command, aggregate history, audit, outbox, Codestra receipt, n8n execution and downstream delivery. Causation IDs connect event chains. Never place PII or secrets in identifiers.

## Metrics

Marketplace funnel:

- request started, submitted, qualified and serviceable;
- match rate and time to match;
- opportunity sent, viewed, accepted, declined and expired;
- quote rate, quote decision time and quote-to-book;
- booking confirmation, cancellation and reschedule;
- job assignment, arrival, completion and dispute;
- verified review and repeat request;
- provider activation, response, completion and retention.

Reliability:

- API latency/error by operation;
- database pool, locks, slow queries and migration head;
- worker queue depth, lease age, retries and crash recovery;
- outbox/inbox status, oldest age and FAILED_TERMINAL count;
- Codestra/Odoo/Klyrow/Telnexa receipt lag;
- credential expiry and capacity conflicts;
- unauthorized and cross-tenant denial counts.

Financial metrics remain hidden or zero while payment capability is disabled.

## Logs and traces

Use structured logs with service, environment, operation ID, actor class, tenant ID, aggregate type/ID, correlation ID, result and safe error code. Redact tokens, customer contact data, addresses, coordinates, attachments, credential documents and provider payloads.

Trace public API, database command, worker lease, gateway delivery and callback processing. Sampling must retain errors and high-risk commands.

## Dashboards and alerts

Dashboards: customer funnel, provider funnel, matching quality, operations SLA, integration reliability, security denials, database/worker health and runtime capabilities.

Page on sustained readiness failure, failed migration, cross-tenant access, unexpected payment traffic, automatic confirmation while disabled, terminal delivery growth, oldest-event SLA breach, credential bypass or backup failure.

## Evidence and retention

Health checks distinguish live, ready and dependency/capability status. Audit, security, financial and consent retention follow policy. Operational logs use bounded retention. Backup evidence includes checksum, isolated restore, migration head, row reconciliation and measured RPO/RTO.
