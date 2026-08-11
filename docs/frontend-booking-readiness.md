# Marketplace and booking readiness

## Live API dependencies

The feature consumes the shared `@breero/api-client`. The live backend must finalize and expose:

- service list/detail and dynamic questions response envelopes
- address validation with authoritative `serviceable`, `address_id`, `service_area_id`, and `legal_entity_code`
- availability search with dated start/end windows
- idempotent booking creation with immutable price snapshot
- payment intent/checkout handoff and customer-safe payment status
- booking status lookup suitable for confirmation polling

The current confirmation deliberately remains `PROCESSING` and does not infer success from a browser redirect. Final webhook-backed polling requires the booking/payment status endpoint.

## Mock/live seam

`apps/web/lib/booking-api.ts` is the single feature adapter. `NEXT_PUBLIC_API_MODE=live` uses the shared transport; otherwise it supplies contract-shaped catalog, address, availability, booking, and payment scenarios. Test-only phrases model service-area, transport, no-availability, and payment failures without embedding fixture JSON in components.

## Final 10%

- Replace catalog content and media with CMS/backend-owned service data.
- Connect the production payment provider redirect/client-secret UI.
- Poll the finalized booking/payment status endpoint with bounded backoff.
- Merge the shared design-system shell/primitives when the frontend-system branch lands.
- Add production analytics events and real customer support/partner destinations.
