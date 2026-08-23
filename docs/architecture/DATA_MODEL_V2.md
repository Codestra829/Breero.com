# BREERO Marketplace V2 Data Model

## Storage authority

PostgreSQL 17 with PostGIS is authoritative. Redis is disposable and may only hold cache, rate limits, availability projections, short-lived locks and Celery state.

Use the actual Alembic head at implementation time. The inspected planning base currently includes migrations through 017_provider_credentials; no implementation PR may assume a revision number without checking the merged target.

## Core tables

### Demand

- project_requests
- project_request_answers
- project_request_attachments
- project_request_status_history

Project requests use UUID primary keys, a public reference, customer/service/address links, status, fulfillment mode, description, urgency, budget range in minor units, currency, preferred window, source, timestamps and an integer version.

### Provider tenancy and trust

- provider_organizations
- provider_memberships
- provider_profiles
- provider_workers
- provider_services
- provider_service_areas
- provider_availability_rules
- provider_availability_exceptions
- credential_requirements
- provider_credentials
- credential_verifications
- provider_documents
- organization_entitlements

Provider geography uses PostGIS geography/geometry with GiST indexes. Jurisdiction, service, subject type and effective dates determine credential requirements.

### Marketplace connection

- matching_runs
- match_candidates
- match_reasons
- opportunities
- opportunity_deliveries
- lead_connections

Matching rows store a reproducible snapshot rather than only a final score. Opportunities preserve every provider invitation and response.

### Commercial and communication

- conversations
- conversation_participants
- messages
- message_attachments
- message_delivery_status
- quotes
- quote_versions
- quote_line_items

Participants are tenant-scoped. Sent quote versions cannot be edited.

### Fulfillment and trust

Existing bookings and jobs gain nullable project_request_id, accepted_quote_id, provider_organization_id and worker_id links. Retain job_status_history, job_assignments, job_notes, job_evidence and job_additional_work.

Add reviews, review_dimensions, review_responses and review_moderation. A unique completed-job relationship prevents duplicate verified reviews.

### Reliability and audit

- integration_events or the existing outbox table
- integration_deliveries
- integration_inbox
- audit_log
- idempotency_records
- runtime_capabilities

## Required constraints

- Unique ProjectRequest public reference.
- Idempotency key plus command scope and request hash uniqueness.
- Unique opportunity per matching run and provider.
- One accepted LeadConnection per applicable opportunity.
- One active accepted quote decision per ProjectRequest according to policy.
- Unique inbox provider plus external_event_id.
- Unique verified review per completed job and eligible customer.
- Tenant key on every provider-owned table.
- Foreign keys use restrictive deletion for financial, audit, job, message and review history.
- Check constraints enforce money ranges, currency format, time ordering and nonnegative capacity.
- Exclusion or equivalent locking constraints prevent overlapping worker reservations.
- Optimistic version checks prevent stale aggregate commands.

## Indexes

- GiST provider service areas and address geography.
- Partial indexes for open requests, active opportunities, unexpired credentials and pending outbox rows.
- Composite indexes for tenant plus status plus updated_at.
- Cursor indexes based on created_at and UUID.
- Search indexes on public provider slug and normalized service fields.

## Migration method

1. Add nullable tables and columns.
2. Deploy dual-compatible code.
3. Backfill in bounded, resumable batches with reconciliation counts.
4. Validate foreign keys and business invariants.
5. Add NOT NULL or stricter constraints only after evidence.
6. Keep v1 reads and writes compatible during the transition.
7. Test upgrade from the current production schema and downgrade where practical.
8. Never test migrations against the production database.
