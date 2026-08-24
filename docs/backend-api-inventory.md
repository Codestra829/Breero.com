# Backend API inventory

The canonical contract is `/openapi.json`. The final source exposes 70 paths, 77 operations, and 77
unique operation IDs. Suggested endpoint names must be mapped to these existing
routes; they must not be duplicated.

| Capability | Canonical route family | State |
|---|---|---|
| Authentication | `/api/v1/auth/*` | Present |
| Customer profile/resources | `/api/v1/customer/*` | Present |
| Address validation | `POST /api/v1/addresses/validate` | Present |
| Catalog/questions | `/api/v1/services*` | Present |
| Availability | `POST /api/v1/availability/search` | Present |
| Guest booking/payment/confirmation | `/api/v1/bookings*` | Present |
| Customer quotes | `/api/v1/customer/quotes*` | Present |
| Payments/refunds/webhook | `/api/v1/payments*` | Present |
| Jobs/work requests | `/api/v1/jobs*` | Present, role protected |
| Matching/assignment | `/api/v1/operations/*` | Present, role protected |
| Vendors/workers | `/api/v1/vendors*` | Present, role protected |
| Finance/payouts | `/api/v1/finance/*` | Present, role protected |
| Integration administration | `/api/v1/integrations/*` | Present, role protected |
| Health | `/health`, `/health/live`, `/health/ready` | Present |
| Public service requests | `POST /api/v1/service-requests` | Present |
| Contact intake | `POST /api/v1/contact` | Present |
| Provider interest | `POST /api/v1/provider-interest` | Present |
| Professional paid leads | `/api/v1/provider/leads*` | Present, provider protected |
| Lead disputes | `/api/v1/provider/leads/{lead_id}/disputes*` | Present, owner protected |
| Customer booking cancellation | `POST /api/v1/customer/bookings/{booking_id}/cancel` | Present |
| Customer payment detail | `GET /api/v1/customer/payments/{payment_id}` | Present |

The customer payment response deliberately excludes the Stripe client secret. Cancellation is
owner-scoped, audited, revokes the guest token, and rejects bookings whose job has progressed beyond
the pre-dispatch states. It does not invent an automatic refund decision.

Professional lead payments use the canonical payment ledger with purpose `PROFESSIONAL_LEAD`.
Server-owned price, currency, provider eligibility, Stripe intent, webhook settlement, and refund
state are linked to the purchase; dispatch offers remain a separate assignment concept.
