# Frontend master readiness

## Integration basis

`codex/frontend-master-final` integrates the system, integration, customer, and booking authority branches. The customer branch was used as the consolidation base because it already contained the system and integration histories; booking was merged with its duplicate root layout, site chrome, CSS tokens, and workspace configuration reconciled manually.

## Backend contract reviewed

The public contract URL `https://api.breero.com/api/v1/openapi.json` did not resolve during integration. Contract alignment on 12 August 2026 therefore used the authoritative source at `origin/codex/backend-master-final` (`9f43287`), specifically its v1 router, auth schemas, customer routes, booking schemas, customer-owned quote decision route, and payment schemas. A deployed OpenAPI/staging run remains a release gate.

The centralized client covers auth registration/login/refresh/logout/password/email lifecycle, services/questions, address validation, availability, booking creation, customer bookings/profile/addresses/quotes/payments, quote decisions, and payment intents/status. Customer-safe payment history uses `/customer/payments`; the generic payment endpoint is not used for account history.

## Mock boundary

Live API mode is the default. Mock data is available only when `NEXT_PUBLIC_API_MODE=mock` is explicit. Production rejects mock mode and a missing/local API URL. The single exception is the explicit `NEXT_PUBLIC_E2E_ALLOW_MOCK=1` test harness used by Playwright; this variable must never be set in staging or production.

## Auth storage trade-off

The current backend returns refresh tokens in JSON rather than an HTTP-only cookie. The frontend centralizes tokens and limits them to `sessionStorage`, rotates through `/auth/refresh`, retries a rejected request once, clears the session on refresh failure, and never uses `localStorage`. This reduces persistence but remains readable by JavaScript. A same-origin BFF or backend HTTP-only cookie contract is recommended before production.

## Known staging blockers

- Public API DNS/OpenAPI and live CORS could not be verified.
- Account dashboard, bookings, quotes, payments, profile, receipts, and saved-address reads now use authenticated live client operations. Contract-shaped fixtures remain only behind the explicit mock test adapter.
- Saved-address creation/editing remains intentionally deferred because the backend requires coordinates; the booking address-validation flow is the safe source for serviceable address coordinates.
- Payment provider handoff is represented by intent creation and an authoritative pending state; Stripe Elements/Checkout and a customer-safe backend confirmation endpoint remain required.
- Quote approval calls the customer-owned backend decision route and additional-payment intent creation uses `quote_id` plus `ADDITIONAL_WORK`; provider UI and webhook-backed confirmation must still be exercised against staging.

## Staging gate

1. Deploy the backend contract that includes the auth/customer lifecycle and publish `/api/v1/openapi.json`.
2. Confirm `NEXT_PUBLIC_API_BASE_URL=https://api.breero.com/api/v1` (the production-safe default) or set the staging API origin; do not set mock or E2E override variables.
3. Configure exact CORS origins for the staging web origin and confirm auth refresh rotation.
4. Configure the Stripe publishable key and customer-safe post-payment status operation.
5. Run frozen install, lint, typecheck, unit tests, production build, Playwright against `E2E_BASE_URL`, and an OpenAPI operation check.
6. Exercise real address serviceability, availability conflict, idempotent booking creation, payment webhook delay/failure, session expiry, quote expiry/decision/payment, refund display, and 401/403/404/409/422/429/500 cases.
7. Run axe smoke and manual Chromium, Firefox, and WebKit checks at 375, 430, 768, 1024, 1280, and 1440 pixels.
