# Provider readiness

Environment variable names on the running API are not credential validation. No values are printed.

| Provider | Configured | Auth test | Callback test | Production ready |
|---|---|---|---|---|
| Stripe | unverified | BLOCKED | BLOCKED | NO |
| Odoo | unverified | BLOCKED | asynchronous code tests only | NO |
| Geocoding | unverified | BLOCKED | n/a | NO |
| Email/SMTP | unverified | BLOCKED | BLOCKED | NO |
| SMS | unverified | BLOCKED | BLOCKED | NO |
| Payouts | absent/unverified | BLOCKED | BLOCKED | NO |
| Object storage | absent/unverified | BLOCKED | BLOCKED | NO |

Required evidence is a successful non-production auth probe, safe provider operation, signed callback
where applicable, duplicate/retry behavior and named owner. Fake adapters remain valid only for
engineering tests. No real charge, payout, or customer communication was initiated.
