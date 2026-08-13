# BREERO nationwide booking policy

BREERO is operated by Codestra LLC (`US01`) in USD. All twelve catalog services are displayed across the fifty U.S. states and Washington, D.C.

An appointment is offered only after Geoapify returns a U.S. address, an active provider has explicit coverage for the service and five-digit ZIP, and that provider has unused capacity in the address's local time. Customer coordinates are not trusted as coverage evidence. Missing geocoding, provider coverage, schedule, payment authorization, or match data fails closed.

- Hours: Monday through Saturday 07:00–19:00; Sunday urgent home-service evaluations 07:00–19:00. BREERO is not an emergency or life-safety service.
- Evaluation: 30 minutes in a reserved 60-minute interval; one appointment per provider per interval.
- Fee: $200 on Monday–Saturday and $300 on Sunday, based on the service-address timezone.
- Work: `QUOTE_REQUIRED`; parts, labor, materials, permits, taxes, and additional work require a separate provider estimate and customer acceptance.
- Confirmation: payment moves a booking to `PENDING_PROVIDER_CONFIRMATION`. Only explicit assignment of the provider holding the reserved slot moves it to `CONFIRMED`.
- No capacity: the customer uses Request Service. The durable service request enters manual dispatch and never promises an appointment.

Provider coverage is replaced atomically through the operator-only canonical route `PUT /api/v1/operations/workers/{worker_id}/booking-coverage`. The API and database both enforce the fixed hours and capacity-one policy.

Cancellation policy:

- at least 24 hours: full evaluation-fee refund;
- less than 24 hours: $49 cancellation fee;
- no-show or cancellation after dispatch: evaluation fee non-refundable;
- provider cancellation: full evaluation-fee refund.

Refund execution remains through the canonical payment/refund authority and must never be simulated by directly editing payment state.
