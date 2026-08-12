# Formal UAT protocol

Run only on isolated staging with live API mode. Production and staging must not set
`NEXT_PUBLIC_API_MODE=mock` or `NEXT_PUBLIC_E2E_ALLOW_MOCK=1`.

## Evidence record

For each case record UTC time, build commits/digests, persona, browser/device, steps, expected
and actual result, request/correlation IDs, and screenshot where useful. Classify defects:
P0 data loss/security/payment corruption; P1 blocked core flow; P2 major issue with workaround;
P3 minor/polish. No unresolved P0/P1 may pass UAT.

## Persona suites

- Customer: discovery through booking, Stripe test payment and backend confirmation, account,
  booking detail, quote/additional payment, refund history, profile, addresses, mobile.
- Partner admin: offers, accept/decline, jobs, worker assignment, availability, earnings,
  payouts, settings, and cross-vendor denial.
- Technician: mobile assigned-job lifecycle, required notes/evidence, additional work, and
  denial on another technician's job.
- Dispatcher/operations: queue, candidates, assignment, timeline, work requests, quote,
  exceptions, lookups; dispatcher must receive 403 on finance-only actions.
- Finance: customer-safe payments/refunds, earnings snapshots, payout review/approval/submit.
- Super admin: users/roles, catalog/questions/pricing/areas, vendors, compensation,
  integrations, audit visibility.

The canonical journey must include provider offer/acceptance, technician transitions,
additional-work quote and payment, earning, payout, and Odoo/outbox delivery. Re-run negative
cases for unserviceable address, no/stale availability, capacity race, booking failure,
payment failure/pending webhook, expired session, unauthorized account, expired quote, and
quote-payment failure.

## Browser and accessibility matrix

Test Chromium, Firefox, WebKit and widths 375, 430, 768, 1024, 1280, and 1440+. Record
horizontal overflow, sticky controls, dialogs, date/time controls and redirects. Manually test
keyboard-only booking/login, focus order/visibility, dialog focus return, error announcements,
labels/headings, contrast and touch targets. Automated Playwright/axe smoke supplements this.

## Performance and concurrency

Capture p50/p95/error rate/request count for services, address validation, availability,
booking create, customer bookings, ops jobs, homepage, service detail, booking transitions and
account. Controlled staging load only; record API/DB/Redis CPU, memory, pool, locks and errors.
Rehearse competing capacity, duplicate webhook, simultaneous assignment/job transition,
outbox claim and duplicate payout submit against PostgreSQL.

## Exit decision

Pass requires all persona suites, canonical and critical negative E2E, browser/mobile and
accessibility gates, green CI, clean migrations, and a verified backup restore. As of
2026-08-12 formal UAT has not run because isolated staging is unavailable: **NOT PASSED**.
