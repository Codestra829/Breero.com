# Production approval matrix

| Group | Status | Owner required | Evidence / remaining concern |
|---|---|---|---|
| Engineering | APPROVED | Engineering release owner | frozen candidate and CI evidence |
| Operations | BLOCKED | named operations owner | disk, UAT, restore/deploy/rollback, alerts |
| Finance | BLOCKED | named finance approver | Stripe/refund/payout callback and reconciliation |
| Security | BLOCKED | named security approver | public internal ports and incomplete live review |
| Infrastructure | BLOCKED | named infrastructure approver | disk, firewall, Caddy, DNS, artifact/staging capacity |
| Business/Product | BLOCKED | named product owner | launch market, service area, vendors, pricing, support and UAT |

Approvals require approver identity, date and linked evidence; Codex cannot self-approve these roles.
