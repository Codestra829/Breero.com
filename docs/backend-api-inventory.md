# Backend API inventory

The live canonical contract is `/openapi.json`. Candidate `2f6eb4e...` exposes 60 paths, 67
operations, and 67 unique operation IDs. Suggested endpoint names must be mapped to these existing
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
| Professional paid leads | — | Not present in canonical contract |
| Lead disputes | — | Not present in canonical contract |
| Customer booking cancellation | — | Not present in canonical contract |

Absent capabilities are recorded as product/API gaps. This staging activation did not invent routes
or duplicate existing operations.

