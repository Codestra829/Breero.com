# BREERO Marketplace V2 Acceptance Tests

## Canonical E2E

Customer enters a problem, creates a ProjectRequest, answers service questions, uploads photos, supplies location and timing, submits, qualifies, matches to three eligible providers, receives controlled opportunities, connects to an accepting provider, exchanges messages, receives versioned quotes, accepts one, schedules, creates a Booking, assigns an eligible worker, completes a Job and submits one verified review.

Marketplace MVP is not complete until this passes with payments disabled.

## Domain and idempotency

- Duplicate ProjectRequest submission creates one downstream aggregate.
- Duplicate Opportunity acceptance creates one LeadConnection.
- Duplicate Quote acceptance creates one accepted decision.
- Duplicate Booking command creates one booking.
- Sent quote revision preserves the prior version.
- Invalid state transitions fail with no partial history/event.
- Aggregate version conflict returns a deterministic conflict.

## Authorization and tenancy

- Provider A cannot access Provider B opportunity, quote, conversation, customer PII or job.
- Customer A cannot access Customer B request.
- Worker cannot execute another provider's job.
- Dispatcher cannot approve payout.
- Support cannot verify credential.
- Unmatched provider cannot receive contact data.
- Attachment URLs require current participant authorization.

## Eligibility and matching

- Zero-provider case stays safe and enters operations.
- Expired, rejected, revoked or missing required credential makes candidate ineligible.
- Suspended provider cannot match.
- PostGIS outside-area address cannot match.
- Expired hold cannot consume capacity.
- Concurrent acceptance and scheduling cannot overbook.
- Stored score components reproduce final rank.

## Integration reliability

- Disabled integration produces PENDING_CONFIGURATION.
- Audited enable safely activates eligible records.
- Duplicate callback produces one business effect.
- Changed-payload replay is rejected.
- Retryable failure retries with the same event ID.
- Worker crash releases after lease expiry and retry succeeds.
- FAILED_TERMINAL is visible to Operations.
- Odoo/n8n outage cannot roll back accepted marketplace state.
- Reconciliation identifies a missing downstream receipt.

## Feature and safety

- Backend rejects payments, paid leads, payouts, automatic assignment, automatic confirmation and marketing while capabilities are false.
- UI does not advertise or enable false capabilities.
- Unexpected Stripe or communication traffic triggers an alert.
- Request-only language never promises booking, provider, price or appointment.

## Database and contract

- Upgrade from the actual current production-compatible Alembic head passes.
- Downgrade passes where practical.
- Backfill is resumable and reconciles counts.
- PostgreSQL/PostGIS integration tests use real constraints and indexes.
- OpenAPI operation IDs are unique.
- V1 compatibility tests pass during migration.
- Event schema compatibility and inbox/outbox uniqueness pass.

## Frontend quality

- Typecheck, lint, unit and production build pass.
- Customer, partner, operations and admin routes have loading, empty, error and forbidden states.
- Keyboard, focus, labels, status announcements and contrast meet the accessibility target.
- Critical flows pass on mobile and desktop.

## Release evidence

Provide exact source SHA, immutable image digest, SBOM, provenance/signature, vulnerability and secret scans, migration/restore evidence, capability snapshot, canary results, dashboards, rollback trigger/owner and an observation-window report. Production activation remains NO-GO until the authorized release owner approves all applicable gates.
