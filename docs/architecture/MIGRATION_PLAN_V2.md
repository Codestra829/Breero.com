# BREERO Marketplace V2 Migration Plan

## Starting point

Base all planning and implementation on codex/breero-production-without-payments after reconciling PR #34. Do not rebuild from the older main snapshot.

The planning branch is documentation only. PR-00 release safety may proceed in parallel. All schema work begins after the safety target is merged.

## Sequential delivery

| Order | Branch | Outcome |
|---:|---|---|
| PLAN | planning/breero-marketplace-v2-unified-architecture | Architecture authority |
| 00 | codex/marketplace-v2-release-safety | Request-only safety and capability authority |
| 01 | codex/marketplace-v2-project-requests | Canonical demand |
| 02 | codex/marketplace-v2-provider-profiles | Provider tenancy and profiles |
| 03 | codex/marketplace-v2-provider-trust-availability | Credentials and capacity |
| 04 | codex/marketplace-v2-matching | Explainable matching |
| 05 | codex/marketplace-v2-opportunities | Controlled connection |
| 06 | codex/marketplace-v2-quotes | Versioned proposals |
| 07 | codex/marketplace-v2-messaging | Participant messaging |
| 08 | codex/marketplace-v2-booking-job-bridge | Downstream fulfillment |
| 09 | codex/marketplace-v2-customer-experience | Customer marketplace |
| 10 | codex/marketplace-v2-provider-saas | Provider operating product |
| 11 | codex/marketplace-v2-ops-command-center | Operations control |
| 12 | codex/marketplace-v2-reviews-trust | Verified reputation |
| 13 | codex/marketplace-v2-analytics | Funnel and quality metrics |
| 14 | codex/marketplace-v2-integration-reliability | Durable inbound/outbound |
| 15 | codex/marketplace-v2-transactions | Payments after approval |
| 16 | codex/marketplace-v2-provider-subscriptions | SaaS monetization |
| 17 | codex/marketplace-v2-azure-modernization | Deferred infrastructure target |

Create each branch from the latest merged target. Avoid a permanent mega-branch or a 17-level branch chain.

## Compatibility strategy

- Keep /api/v1 working.
- Adapt v1 service requests into ProjectRequest.
- Add nullable V2 links to bookings/jobs.
- Dual-write only through one domain service and one transaction; never duplicate business logic in routes.
- Backfill with resumable jobs and reconciliation totals.
- Switch reads only after shadow comparison.
- Publish deprecation telemetry before removing a path.
- Preserve historical identifiers and audit history.

## Release gates

Every PR requires lint, types, unit tests, PostgreSQL/PostGIS integration, migration upgrade, authorization and negative tests, idempotency, relevant concurrency, OpenAPI compatibility, observability and rollback notes.

No phase enables payments, payouts, paid leads, automatic assignment, automatic confirmation, marketing, email or SMS merely because its schema exists. Capability activation is a separate approved release with canary and reconciliation evidence.
