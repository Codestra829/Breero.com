# Frontend API contract handoff

Generate the canonical contract with `python scripts/generate_openapi.py`; the deployed source of
truth is `/openapi.json` under the API origin. CI rejects missing or duplicate operation IDs.

Frontend clients use `/api/v1/customer/` for owner-scoped profile, address, booking, quote,
payment, and refund views. Refresh tokens are opaque rotating credentials; replay of a rotated
token revokes its family. Payment purpose is explicit (`BOOKING_DIAGNOSTIC` or
`QUOTE_ADDITIONAL_WORK`). Quote approval can enter `APPROVED_PENDING_PAYMENT` and is not payment
capture. Finance and integration administration routes enforce their declared RBAC roles.

Regenerate typed clients when the contract artifact changes. Do not retain mocks that omit payment
purpose, quote payment state, refund state, pagination containers, or refresh-token rotation.
