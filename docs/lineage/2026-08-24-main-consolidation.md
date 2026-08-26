# BREERO Main Lineage Reconciliation

This record has two distinct purposes:

1. preserve the immutable lineage snapshot captured immediately after PR #34 entered `main` on 2026-08-24; and
2. record the post-reconciliation status verified on 2026-08-26.

The snapshot classifications describe what was true **before** PRs #38–#42 were reconstructed. They must not be read as current branch status.

## 1. Immutable post-#34 snapshot — 2026-08-24

```text
BASELINE_MAIN_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
PR_34_MERGE_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
PR_34_ACCEPTED_HEAD=b3de8e1d025e87540fcf2f38f973ab076a282722
MIGRATION_HEAD_AT_CONSOLIDATION=017_provider_credentials

PR_15_STATUS_AT_SNAPSHOT=SUPERSEDED
PR_16_STATUS_AT_SNAPSHOT=SUPERSEDED
PR_38_STATUS_AT_SNAPSHOT=REBASE_REQUIRED
PR_39_STATUS_AT_SNAPSHOT=REBASE_DOCS
PR_40_STATUS_AT_SNAPSHOT=REBASE_DOCS
PR_41_STATUS_AT_SNAPSHOT=PARTIAL_REUSE
PR_42_STATUS_AT_SNAPSHOT=PARTIAL_REUSE

PRODUCTION_DEPLOYED=NO
CAPABILITIES_ACTIVATED=NO
```

### Snapshot classification rationale

- **PR #15 — backend master integration:** contained in the accepted #34 baseline; do not merge or cherry-pick again.
- **PR #16 — frontend master integration:** contained in the accepted #34 baseline; do not merge or cherry-pick again.
- **PR #38 — P0 API foundation:** additive V2/API foundation work existed on a diverged branch and required reconstruction on accepted `main`.
- **PR #39 — Marketplace V2 authority:** documentation and scope-guard work remained useful but required reconstruction on accepted `main`.
- **PR #40 — Odoo CRM authority:** the additive authority document remained useful, while old baseline content did not.
- **PR #41 — backend bootstrap:** only the conservative reconciliation tool was a candidate for selective reuse; generated scaffolding required re-evaluation.
- **PR #42 — frontend bootstrap:** only route/safety authority was a candidate for selective reuse; placeholder shells, layout/config changes, and generated workspace files were unsafe to merge over the richer accepted frontend.

The required rule at this point was reconstruction, not blind rebase/merge.

## 2. Verified post-reconciliation status — 2026-08-26

```text
ACCEPTED_MAIN_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
CURRENT_MIGRATION_HEAD=017_provider_credentials

PR_38_HEAD=2318b15115df5066592ad2f8653ba17435d6b15e
PR_38_STATUS=READY_FOR_INDEPENDENT_REVIEW
PR_38_BACKEND_RUN=32935147544_PASS
PR_38_FRONTEND_RUN=32935147530_PASS

PR_39_HEAD=d617fc9ec6f9bb611cc76d6871f52b5dfb1ae503
PR_39_STATUS=DRAFT_DOCUMENTATION_AUTHORITY
PR_39_SCOPE_GUARD=PASS

PR_40_HEAD=4989e3bae2f122e19d62d5bf404ef7065db762f0
PR_40_STATUS=DRAFT_DOCUMENTATION_AUTHORITY

PR_41_HEAD=e7cfc47c17d31d2ba82a02dc86c026be29264a20
PR_41_STATUS=BLOCKED_TOOLING_REVIEW

PR_42_HEAD=9ebed8c91de5d9c9b0e5e14b470b724ba5971180
PR_42_STATUS=READY_FOR_INDEPENDENT_DOCUMENTATION_REVIEW

PRODUCTION_DEPLOYED=NO
CAPABILITIES_ACTIVATED=NO
```

### PR #38 outcome

PR #38 was reconstructed directly on accepted `main`. The initial frontend failure was a stale request-only OpenAPI guard that rejected three manual-scheduling routes already accepted by PR #34. The guard now treats those routes as required while continuing to reject payment mutations.

Exact-head backend and frontend production gates pass, including contract verification, production build, and full Playwright E2E. CI success does not replace independent review or branch-protection gates.

### PR #39 outcome

PR #39 is the current Marketplace V2 documentation and BREERO scope-guard authority. The old pre-consolidation application tree was discarded. Its scope guard passes, but documentation remains unapproved until independently reviewed.

### PR #40 outcome

PR #40 retains only the Odoo campaign CRM authority document. BREERO PostgreSQL/PostGIS remains authoritative marketplace state, and Odoo remains a CRM projection/workspace. No Odoo installation, upgrade, external send, or runtime change is included.

### PR #41 outcome and blocker

PR #41 retains only `scripts/bootstrap_breero_backend.py`; no generated scaffolding was applied. It is not review-ready because:

- `--apply` reports but does not reject a dirty worktree;
- `--allow-other-branch` can permit application outside the expected feature branch, including a protected branch;
- the changed script path is outside current workflow triggers;
- focused safety tests are absent.

Required repair: fail closed for dirty apply mode and protected branches, add tests, and add CI coverage. Do not apply scaffolding while making that repair.

### PR #42 outcome

PR #42 retains only two documentation files. The route registry now labels all Marketplace V2 paths as target-state rather than current runtime, protects existing accepted routes, separates navigation from backend authority, forbids placeholders, and enumerates all high-risk capabilities as disabled. It changes no frontend runtime code.

## 3. Historical PR cleanup

The following obsolete pre-consolidation PRs were closed without merging or deleting their branches:

```text
#21 production NO-GO evidence
#22 old architecture/staging boundary work
#23 blocked staging proof
#24 old public-site launch candidate
#25 old staging certification candidate
#33 old quote-only scheduling branch
#36 superseded Marketplace V2 planning authority
```

Their branches and discussions remain available for audit. Current infrastructure and UAT gates remain issues #17–#19 and require fresh read-only evidence.

## 4. Current review and implementation sequence

```text
1. Obtain independent review of unchanged PR #38 head.
2. Resolve review findings and rerun exact-head checks after any code change.
3. Merge only after approval, required checks, and branch-protection gates pass.
4. Verify the new main SHA and checks after merge.
5. Independently review the documentation authorities (#39, #40, #42, and this record).
6. Repair #41 as a tested fail-closed tool before considering it review-ready.
7. Begin production identity/authentication and authorization as the first new engineering workstream.
8. Do not start provider, matching, messaging, transaction, or activation work early.
```

## 5. Next engineering boundary

The first new implementation branch after the P0 API foundation is production identity/authentication and authorization only:

```text
OIDC production enforcement
canonical issuer validation
external_identities
immutable issuer + subject binding
JWKS/discovery cache
unknown-kid refresh
local-production-auth shutdown
Principal construction
/api/v2/me
tenant membership and RBAC authority
production auth configuration
negative authentication and authorization tests
```

Explicit non-scope:

```text
NO provider network
NO matching
NO opportunities
NO messaging
NO reviews
NO object storage/documents
NO live webhooks/adapters
NO payments
NO payouts
NO paid leads
NO instant booking
NO automatic assignment
NO automatic confirmation
NO marketing
NO unrestricted external sends
NO capability activation
```

This record does not deploy, migrate production data, merge an implementation PR, or activate any capability.
