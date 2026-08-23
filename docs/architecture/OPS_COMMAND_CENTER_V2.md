# BREERO Marketplace V2 Operations Command Center

## Mission

Operations provides controlled intervention without corrupting marketplace history or bypassing trust rules.

## Primary areas

Requests, Matching, Jobs, Providers, Exceptions and Map.

## Queues

- unmatched;
- awaiting provider;
- awaiting quote;
- scheduling;
- unassigned;
- late;
- at risk;
- credential issue;
- stale opportunity;
- integration failure;
- terminal outbox or inbox failure.

Each queue shows SLA age, owner, latest event, next action and capability state.

## Matching inspector

Show candidate, eligible result, gate reasons, distance/service-area evidence, credentials, availability, capacity, score breakdown, rank, invitation history and algorithm version. Customer PII remains masked until connection policy permits disclosure.

## Commands

Approved commands include qualify, rerun matching, send or withdraw opportunity, record provider response, request customer information, verify credential, suspend provider, propose schedule, assign eligible worker, cancel, escalate and retry safe integration delivery.

Commands require permission, current aggregate version, reason code, bounded note and idempotency key. The result includes the new version and audit reference.

## Guardrails

- No generic status editor.
- No assignment to an ineligible provider or worker.
- No credential bypass.
- No payment or payout command while capabilities are disabled.
- No message outside consent and communication-purpose policy.
- No deletion of source request, history, audit or failed-delivery evidence.
- Bulk actions preflight every target and report partial failure without silent skipping.

## Incident and reconciliation

The exception center links domain timeline, audit, outbox/inbox attempts, Codestra receipt and downstream projection status. Operators can park, replay a retryable event, mark a documented terminal disposition or escalate. Changed-payload replays are never forced through.

## Service objectives

Suggested initial operational targets are measurable after baseline:

- request qualification p95 under 15 minutes during staffed hours;
- terminal integration failure visible under 5 minutes;
- stale opportunity and credential expiry alerts before customer impact;
- zero unauthorized cross-tenant reads or manual trust bypasses.
