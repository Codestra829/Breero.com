# BREERO Main Lineage Reconciliation — 2026-08-24

This record freezes the accepted application baseline immediately after PR #34 and classifies the older/follow-on branches before any modification of PRs #38–#42.

```text
BASELINE_MAIN_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
PR_34_MERGE_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
PR_34_ACCEPTED_HEAD=b3de8e1d025e87540fcf2f38f973ab076a282722
CURRENT_MIGRATION_HEAD=017_provider_credentials

PR_15_STATUS=SUPERSEDED
PR_16_STATUS=SUPERSEDED

PR_38_STATUS=REBASE_REQUIRED
PR_39_STATUS=REBASE_DOCS
PR_40_STATUS=REBASE_DOCS
PR_41_STATUS=PARTIAL_REUSE
PR_42_STATUS=PARTIAL_REUSE

PRODUCTION_DEPLOYED=NO
CAPABILITIES_ACTIVATED=NO
```

## Evidence and classification

### PR #15 — backend master integration

GitHub closed/marked #15 merged when #34 entered `main`. Its backend lineage is contained in the accepted baseline. Do not merge or cherry-pick #15 again.

Classification: `SUPERSEDED`.

### PR #16 — frontend master integration

GitHub closed/marked #16 merged when #34 entered `main`. Its frontend lineage is contained in the accepted baseline. Do not merge or cherry-pick #16 again.

Classification: `SUPERSEDED`.

### PR #38 — Marketplace V2 P0 API foundation

Comparison against new `main` shows the branch is diverged: it carries 10 commits not in `main` and is 27 commits behind the accepted baseline. Its additive work includes the V2 API boundary, command/context/domain primitives, error contract, capability parity, OpenAPI changes, and focused tests.

Classification: `REBASE_REQUIRED`.

Rules:
- rebase/reconstruct on accepted `main`;
- retain only additive P0/API foundation changes;
- preserve all PR #34 request-only safety gates;
- do not introduce identity, provider, matching, quote, storage, webhook, payment, payout, or activation scope into this reconciliation.

### PR #39 — Marketplace V2 production implementation authority

Comparison against new `main` shows the branch is diverged: 12 commits ahead of its old base and 27 commits behind current `main`. The changes are documentation/scope-guard authority and remain useful.

Classification: `REBASE_DOCS`.

Rules:
- rebase documentation onto accepted `main`;
- preserve the canonical issuer `https://auth.codestra.co/realms/codestra`;
- do not let documentation merge imply implementation, deployment, certification, or activation.

### PR #40 — Odoo campaign CRM authority

Comparison against new `main` shows one additive documentation commit and 27 commits of baseline drift.

Classification: `REBASE_DOCS`.

Rules:
- rebase the Odoo authority document only;
- BREERO PostgreSQL/PostGIS remains authoritative marketplace state;
- Odoo remains CRM projection/workspace only;
- no Odoo deployment or external-send activation is implied.

### PR #41 — backend production bootstrap

Comparison against new `main` shows one additive file (`scripts/bootstrap_breero_backend.py`) and 170 commits of baseline drift. The script is useful as a safe dry-run/reconciliation tool, but its generated package boundaries must be evaluated against the now-richer backend before any application.

Classification: `PARTIAL_REUSE`.

Patch categories:

```text
scripts/bootstrap_breero_backend.py=STILL_NEEDED_AS_RECONCILIATION_TOOL
generated backend scaffolding=RECHECK_AGAINST_MAIN
existing richer domains/integrations=ALREADY_IN_MAIN_OR_NEWER_IMPLEMENTATION
blind branch merge=OBSOLETE
```

### PR #42 — frontend production bootstrap

Comparison against new `main` shows six additive bootstrap commits and 170 commits of baseline drift. The route inventory, bootstrap safety documentation, and portions of the route/bootstrap tooling remain useful; app configuration, layouts, lockfile/workspace changes, and shell pages must be reconciled against the accepted richer frontend.

Classification: `PARTIAL_REUSE`.

Patch categories:

```text
canonical route inventory=STILL_NEEDED
bootstrap safety docs/tooling=STILL_NEEDED
route shells=REVIEW_PER_ROUTE
app layouts/config/package files=CONFLICTS_WITH_NEWER_IMPLEMENTATION_OR_REQUIRES_MANUAL_RECONCILIATION
pnpm-lock/turbo/workspace changes=REGENERATE_FROM_ACCEPTED_MAIN_IF_NEEDED
blind branch merge=OBSOLETE
```

## Required sequence from this baseline

```text
1. Verify baseline main
2. Run baseline CI/smoke without deployment
3. Rebase/reconstruct PR #38 on main
4. Rebase PR #39 documentation on main
5. Rebase PR #40 documentation on main
6. Reconcile #41 patch selectively
7. Reconcile #42 patch selectively
8. Close/supersede obsolete branches only after unique work is accounted for
9. Start production identity/authentication as the first new engineering workstream
```

## Next engineering branch boundary

The first new implementation branch after consolidation is production identity/authentication only:

```text
OIDC production enforcement
external_identities
issuer + subject binding
JWKS/discovery cache
unknown-kid refresh
local-production-auth shutdown
Principal construction
/api/v2/me
production auth configuration
negative authentication tests
```

Explicit non-scope for that branch:

```text
NO provider network
NO matching
NO quotes
NO object storage/documents
NO webhooks/adapters
NO payments
NO payouts
NO paid leads
NO instant booking
NO automatic assignment
NO capability activation
```

This record does not deploy or activate anything.
