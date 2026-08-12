# @breero/api-client

Typed API client shared by BREERO frontend applications.

Modules should mirror backend boundaries:

- auth
- services
- addresses
- availability
- bookings
- customer
- partner
- ops
- payments
- finance

Frontend applications must not scatter raw API URLs through components. Centralize transport, authentication, errors and typed contracts here.

Use `createConfiguredApi(process.env, options)` as the application seam. It selects the live transport or contract-shaped mock scenario from `NEXT_PUBLIC_API_MODE`. Live requests share timeout, cancellation, authentication, normalized errors and idempotency behavior. Automatic retries are limited to idempotent reads; booking, quote and payment writes are never blindly retried.

Backend contract gaps and staging requirements are tracked in `docs/frontend-integration-readiness.md`.
