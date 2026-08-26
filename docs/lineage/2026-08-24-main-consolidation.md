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

PR_39_HEAD=b1a0865918971e3ce16f62aaeda38bd6001a1308
PR_39_STATUS=READY_FOR_INDEPENDENT_DOCUMENTATION_REVIEW
PR_39_SCOPE_GUARD_RUN=32936351888_PASS

PR_40_HEAD=132d27b91d56748e82d0e6b4eb6d53fb1ce8db0e
PR_40_STATUS=READY_FOR_INDEPENDENT_DOCUMENTATION_SECURITY_REVIEW

PR_41_HEAD=969b3d7fd5b87fd7a0df7e4f499cd452e0e1c6fa
PR_41_STATUS=READY_FOR_INDEPENDENT_CODE_SECURITY_REVIEW
PR_41_BOOTSTRAP_TOOL_RUN=32936774159_PASS
PR_41_UNIT_TESTS=13_PASS
PR_41_SCAFFOLDING_APPLIED=NO

PR_42_HEAD=9ebed8c91de5d9c9b0e5e14b470b724ba5971180
PR_42_STATUS=READY_FOR_INDEPENDENT_DOCUMENTATION_REVIEW

ALL_POST_CONSOLIDATION_PRS_REVIEWABLE=YES
MERGE_READY=NO
PRODUCTION_DEPLOYED=NO
CAPABILITIES_ACTIVATED=NO
```

Every review-ready status above means the branch is prepared for independent review. It does not mean an approval exists, the repository ruleset is satisfied, or a merge is authorized.

### PR #38 outcome

PR #38 was reconstructed directly on accepted `main`. The initial frontend failure was a stale request-only OpenAPI guard that rejected three manual-scheduling routes already accepted by PR #34. The guard now treats those routes as required while continuing to reject payment mutations.

Exact-head backend and frontend production gates pass, including contract verification, production build and full Playwright E2E. CI success does not replace independent review or branch-protection gates.

### PR #39 outcome

PR #39 is the current Marketplace V2 documentation and BREERO scope-guard authority. It now binds status to the accepted quote-only/operator-confirmed scheduling baseline, includes a deny-by-default authorization matrix, defines evidence for each production/readiness/activation gate, and records the current system-of-record and identity boundaries. The old pre-consolidation application tree was discarded. Its exact-head BREERO scope guard passes.

### PR #40 outcome

PR #40 retains the Odoo campaign CRM implementation authority and an Odoo 19 platform/review-gate companion. BREERO PostgreSQL/PostGIS remains authoritative marketplace state, while Odoo remains a campaign CRM projection/workspace. The documents require exact Odoo 19 build/dependency evidence, multi-company/tenant record rules, mail safety, upgrade/rollback tests, and separately approved channel activation. No Odoo installation, upgrade, external send or runtime change is included.

### PR #41 outcome

PR #41 retains and hardens `scripts/bootstrap_breero_backend.py`; no generated scaffolding was applied.

The repaired tool:

- remains dry-run by default;
- rejects dirty apply mode;
- rejects apply mode on protected/production/release branches even with override;
- rejects detached HEAD, path escape, cross-project scope and non-identical overwrite;
- applies only missing structural boundaries;
- has 13 focused safety tests and a dedicated compile/unit/dry-run CI gate.

Exact-head workflow run `32936774159` passes. The workflow never invokes `--apply`.

### PR #42 outcome

PR #42 retains only two documentation files. The route registry labels all Marketplace V2 paths as target-state rather than current runtime, protects existing accepted routes, separates navigation from backend authority, forbids placeholders, and enumerates all high-risk capabilities as disabled. It changes no frontend runtime code.

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

## 4. Current governance blocker

Issue #45 records a repository ruleset defect:

```text
ACTIVE_RULESET=protected-main-production-release
REQUIRED_CONTEXT=quality
BACKEND_WORKFLOW_CONTEXT=quality
FRONTEND_WORKFLOW_CONTEXT=quality
DOCUMENTATION_ONLY_CONTEXT=ABSENT
```

This creates ambiguous duplicate ownership for mixed code PRs and a missing required context for documentation-only PRs. Until workflows and ruleset `20802489` are repaired and verified together, a GitHub “mergeable” result is not proof that the required-check gate passed.

## 5. Current review and implementation sequence

```text
1. Obtain independent review of unchanged PR #38 exact head.
2. Resolve any findings and rerun exact-head checks after every code push.
3. Repair and verify issue #45 without weakening backend/frontend gates.
4. Merge #38 only after valid approval, resolved threads and ruleset requirements pass.
5. Verify the new main SHA and exact checks after merge.
6. Independently review documentation/tooling authorities #39, #40, #41, #42 and this lineage record.
7. Merge each only in dependency-safe order and only after its own valid review/check gates.
8. Begin production identity/authentication and authorization as the first new engineering workstream.
9. Do not start provider, matching, messaging, transaction or activation work early.
```

## 6. Next engineering boundary

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

This record does not deploy, migrate production data, merge an implementation PR, modify the active ruleset, or activate any capability.
