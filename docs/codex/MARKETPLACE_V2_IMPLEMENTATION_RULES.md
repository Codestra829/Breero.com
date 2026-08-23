# BREERO Marketplace V2 Implementation Rules

## Architecture

1. Inspect current code, migrations, OpenAPI and shared types before changing anything.
2. Extend the modular monolith; do not create premature microservices.
3. Keep routes thin and business rules in domain services.
4. Separate SQLAlchemy models, Pydantic schemas, repositories, commands, policies and events.
5. Use one authoritative aggregate for each business fact.

## Database

6. Use Alembic for every schema change and the actual merged head.
7. Additive first; backfill before enforcing new constraints.
8. Repositories flush but do not own application commits.
9. Command boundaries atomically commit state, history, audit and outbox.
10. Use row locks, unique constraints and aggregate versions for concurrency.
11. Redis, search, Odoo and n8n are never authoritative.

## API and events

12. Preserve /api/v1 during migration and add /api/v2 deliberately.
13. Require Idempotency-Key and request hash for commands.
14. No generic status PATCH.
15. Regenerate OpenAPI and typed clients in the same PR.
16. Version events and validate schema compatibility.
17. Exactly-once external delivery is not claimed.

## Security

18. Use auth.codestra.co only; remove auth.codestra.agency.
19. Enforce permission and tenant scope server-side on every query.
20. Entitlements do not replace RBAC.
21. Minimize PII before LeadConnection.
22. Protect attachments and credentials with explicit authorization and short-lived access.
23. Never commit or log secrets, tokens, contact data or document contents.

## Integrations

24. Use transactional outbox and idempotent inbox.
25. Disabled integrations park as PENDING_CONFIGURATION.
26. Workers lease before delivery and recover after lease expiry.
27. Codestra middleware requires mTLS, HMAC-V2, replay protection and exact tenant/environment/scope.
28. Odoo and n8n cannot overwrite marketplace state.
29. Capability creation does not imply capability activation.

## Frontend

30. UI copy and controls must reflect runtime capability.
31. Request is not booking; opportunity is not connection; quote is not confirmation.
32. Provide accessible loading, empty, error, forbidden, stale and recovery states.
33. Reuse packages/ui and typed API clients.
34. Test mobile, desktop, keyboard and screen-reader behavior.

## Git and delivery

35. Small sequential PRs; no unrelated refactors.
36. Do not create one permanent V2 mega-branch.
37. Record baseline/final SHA, migration head, tests and known risks.
38. Never deploy from a planning branch.
39. Keep external side effects disabled unless explicitly authorized.
40. Stop on migration drift, unauthorized access, secret exposure or unexpected payment/communication traffic.
