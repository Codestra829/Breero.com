# Frontend integration readiness

Status: integration foundation is staging-ready; feature routes and several customer APIs remain owned dependencies.

## Configuration

- `NEXT_PUBLIC_API_BASE_URL` must include `/api/v1` (default `http://localhost:8000/api/v1`).
- `NEXT_PUBLIC_API_MODE=live|mock` selects one client-wide seam. Mock data is injected into `createConfiguredApi`; it is never scattered through pages.
- `NEXT_PUBLIC_API_TIMEOUT_MS` defaults to 12 seconds and is constrained to 1–60 seconds.
- Only browser-safe values belong in `NEXT_PUBLIC_*`; Stripe, JWT and provider secrets remain server-side.

## Implemented backend contracts

Typed live client coverage matches `origin/codex/backend-90` for:

- auth register, login and current user;
- services, service detail and dynamic questions;
- address validation and availability search;
- idempotent booking creation and authenticated customer booking list/detail;
- idempotent payment-intent creation and authoritative payment lookup.

Transport behavior is centralized: bearer auth, request cancellation, timeouts, request IDs, FastAPI/domain error normalization, session-expiry callback, and retry of safe reads only. Booking, auth, address, availability, quote approval and payment writes are never automatically retried.

## Exact backend/API dependencies

The client exposes stable frontend interfaces for the following, but `origin/codex/backend-90` does not yet implement their routes:

- `GET/PATCH /customers/me/profile`;
- `GET /customers/me/quotes`, `GET /customers/me/quotes/{id}`, `POST /customers/me/quotes/{id}/approve`;
- customer payment history/list (only payment lookup by known ID exists);
- password reset, email verification, refresh/logout/session revocation;
- booking detail enrichment: address/service display data, payment summary, job/technician, status timeline and support actions;
- payment checkout URL/SDK contract (current intent returns a provider `client_secret`).

Until these land, customer features should use the one mock adapter and must not infer successful payment from a redirect. Poll/read authoritative booking or payment state.

## Test, accessibility and performance state

- Unit/contract suites cover normalized failures, bearer headers, idempotency, safe retry policy, timeout behavior, mock/live switching and the full mocked booking-to-payment journey.
- Playwright is configured for desktop Chromium and iPhone 13. The baseline smoke asserts a visible main landmark/heading and horizontal overflow behavior; feature authorities should extend it as their routes land.
- Current branch has only the scaffold homepage, so dialog, sheet, form-label, booking/account keyboard flows and empty/error views cannot yet be audited here. Those are explicit follow-ups against frontend authorities 1–3.
- Production output is fully static at the scaffold stage, with approximately 102 kB shared first-load JavaScript and no route-specific client bundle. Re-audit waterfalls, images, hydration boundaries and bundle growth after feature branches integrate.
- Analytics and error reporting are vendor-neutral adapters. No live analytics/reporting credential is required; production vendor selection is a remaining deployment decision.

## External staging inputs

Required outside this repository: deployed API URL/CORS origin, production auth/JWT configuration, Stripe publishable/payment integration choice, and analytics/error-reporting vendor credentials if enabled.
