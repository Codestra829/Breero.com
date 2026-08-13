# BREERO production manual-dispatch runbook

This release accepts service requests; it does not create bookings, collect payments,
assign providers automatically, or promise appointment times. Dispatcher access requires
the `breero_dispatcher` or `breero_admin` Keycloak realm role. The queue is available at
`GET /api/v1/operations/dispatcher/queue` and must never be exposed publicly.

## Queue review

1. Work oldest requests first, prioritizing safety issues and requests marked for follow-up.
2. Confirm the request remains `REQUESTED` and `PENDING_MANUAL_DISPATCH`.
3. Treat an unverified address as manual-validation work. Never infer an appointment from
   an address, ZIP code, Geoapify response, or requested time alone.
4. Record every contact attempt and material decision in the audit history. Do not copy
   personal addresses or contact details into general logs, chat, or ticket titles.

## Address verification

Compare street, city, state/district, five-digit ZIP, and service-address time zone. If
Geoapify is unavailable, rate-limited, ambiguous, or rejects the address, retain the
request for manual validation. Unsupported or non-U.S. addresses cannot proceed to a U.S.
provider match. Never mark an appointment confirmed from an unverified address.

## Customer follow-up

Use only the consented transactional channel. Confirm requested scope, address, preferred
timing, and that BREERO has not yet confirmed a provider, price, or appointment. Record the
attempt, timestamp, outcome, and required next action. Marketing, SMS, email automation,
and callbacks remain disabled for this release.

## Provider matching and capacity

Use only the approved production provider roster. Verify service capability, license and
insurance requirements, exact ZIP coverage, and explicit capacity for the customer’s local
date/time. Providers, workers, dispatchers, and administrators are never auto-enrolled or
auto-assigned. With an empty roster or no verified capacity, leave the request unassigned.

## Estimate and quote coordination

Every job is quote-required. Pricing shown on BREERO is informational; the independent
provider supplies the final job price. Do not request a payment method or represent any
booking, evaluation, lead, or service fee as collected online.

## Appointment confirmation

Only an authorized operator may confirm after the address, approved provider, coverage,
capacity, scope, quote communication, and customer acceptance are all recorded. Until then,
the request must not become `CONFIRMED`, `PROVIDER_ASSIGNED`, `PAID`, or `SCHEDULED`.

## Cancellation and closure

Record who requested cancellation, when, the reason, contact outcome, and final disposition.
Closure must retain the immutable request and audit history. No automatic refund applies
because online payments are disabled.

## Incident handling

For unauthorized access, PII leakage, duplicate/conflicting submissions, unexpected Stripe
traffic, automatic confirmation, or fake assignment: stop the affected release path, preserve
logs and database evidence without exposing secrets, notify the Codestra LLC incident owner,
and use the exact rollback manifest. Do not delete the original request or audit records.
