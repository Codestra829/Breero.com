# BREERO Main Lineage Reconciliation

This record separates:

1. the immutable snapshot captured after PR #34 entered `main` on 2026-08-24; and
2. the final review-preparation state verified on 2026-08-26.

Historical classifications must not be read as current branch status.

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

PRs #15 and #16 were contained in the accepted #34 baseline. PRs #38–#42 had useful additive material but were not safe blind-merge candidates; they required reconstruction directly on accepted `main`.

## 2. Final review-preparation state — 2026-08-26

```text
ACCEPTED_MAIN_SHA=8071572c90905d98894ab1a4cafe99a4178f7dd8
CURRENT_MIGRATION_HEAD=017_provider_credentials

PR_38_HEAD=954b3f05cbbf21c9176801f1db35cb5b80b78f16
PR_38_BACKEND_RUN=32937169770_PASS
PR_38_FRONTEND_RUN=32937169756_PASS
PR_38_UNRESOLVED_THREADS=0

PR_39_HEAD=c17741341f4109479f9bfac25c47c62558b6eb84
PR_39_SCOPE_GUARD_RUN=32937675558_PASS
PR_39_UNRESOLVED_THREADS=0

PR_40_HEAD=5cbc2d386dce1ec8063641d0e3c7d82d8a2320f4
PR_40_UNRESOLVED_THREADS=0

PR_41_HEAD=11183c7ef9b6bc2a0ce4b12aeadb8fd31c4e5125
PR_41_BOOTSTRAP_TOOL_RUN=32938001986_PASS
PR_41_UNIT_TESTS=20_PASS
PR_41_UNRESOLVED_THREADS=0
PR_41_SCAFFOLDING_APPLIED=NO

PR_42_HEAD=9ebed8c91de5d9c9b0e5e14b470b724ba5971180
PR_42_UNRESOLVED_THREADS=0

ALL_POST_CONSOLIDATION_PRS_REVIEWABLE=YES
INDEPENDENT_APPROVAL_ON_CURRENT_HEADS=NO
MERGE_READY=NO
PRODUCTION_DEPLOYED=NO
CAPABILITIES_ACTIVATED=NO
```

“Reviewable” means the branch is prepared for fresh independent review. It does not mean approval exists, the active ruleset is satisfied, or merge/deployment is authorized.

### PR #38 — P0 API foundation

PR #38 was reconstructed on accepted `main`.

The stale request-only OpenAPI guard was corrected to preserve the three manual-scheduling routes accepted by PR #34 while continuing to reject payment mutations.

Automated review then found two V2 error-contract defects. The final head now:

- normalizes unexpected V2 failures into the stable correlated JSON envelope without leaking implementation details;
- preserves `Allow`, `Retry-After`, `WWW-Authenticate`, and other HTTP exception headers;
- adds regression coverage for 405, 429, and unexpected 500 behavior.

Both production workflows pass and all review threads are resolved.

### PR #39 — Marketplace V2 implementation authority

PR #39 is the current Marketplace V2 documentation and BREERO scope-guard authority.

Its final review repair:

- makes expired `PROCESSING` outbox rows reclaimable;
- requires a fresh claim token for every claim generation and exact-token finalization;
- recycles expired idempotency records before active replay/conflict behavior;
- standardizes `quote.accept` as the canonical customer quote-decision permission;
- replaces unsafe copy/paste pseudo-code with a binding reliability contract that extends existing BREERO services.

The exact-head BREERO scope guard passes and all review threads are resolved.

### PR #40 — Odoo 19 campaign CRM authority

PR #40 remains documentation-only.

The final contract:

- extends `odoo-addons/breero_crm` version `19.0.1.0.0`;
- preserves the existing `breero.sync.event` delivery contract;
- forbids a disconnected replacement addon tree;
- enforces one authoritative campaign membership per `(campaign_id, user_id)` with separate history;
- requires validated first-class company, BREERO tenant, and campaign scope on accepted integration rows;
- retains BREERO PostgreSQL/PostGIS as authoritative marketplace state;
- keeps external email/SMS, telephony writes, and automated execution disabled.

All review threads are resolved. No Odoo module was installed or upgraded.

### PR #41 — fail-closed backend bootstrap tool

PR #41 retains only the hardened tool, tests, and dedicated workflow. No scaffold was applied.

The final tool:

- defaults to dry-run;
- independently validates README and origin repository identity;
- requires origin repository name `Breero.com`;
- permits the other-branch override only in dry-run mode;
- requires the exact feature branch for apply mode;
- rejects dirty, detached, protected/release, path-escape, and non-identical-overwrite contexts;
- has 20 safety tests plus compile and real dry-run smoke coverage.

The exact-head workflow passes and all review threads are resolved.

### PR #42 — frontend target-route and safety authority

PR #42 retains only two documentation files. It:

- labels Marketplace V2 routes as target-state rather than current runtime;
- protects existing accepted routes;
- separates frontend navigation from backend identity, tenant, permission, record-policy, and capability authority;
- forbids placeholder success pages and fake portal data;
- enumerates all high-risk capabilities as disabled.

It changes no frontend runtime code and has no unresolved review threads.

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

Their branches and discussions remain available for audit.

## 4. Open P1 gates

```text
#17 production-host disk/capacity safety
#18 isolated staging/UAT/DNS/provider readiness
#19 public data-plane ports and production database revision
#45 required-check/ruleset governance
```

Issues #17–#19 require fresh read-only evidence. August 12 host observations are historical until revalidated on the actual approved infrastructure.

Issue #45 records this ruleset defect:

```text
ACTIVE_RULESET=protected-main-production-release
RULESET_ID=20802489
REQUIRED_CONTEXT=quality
BACKEND_WORKFLOW_CONTEXT=quality
FRONTEND_WORKFLOW_CONTEXT=quality
DOCUMENTATION_ONLY_CONTEXT=ABSENT
```

This creates ambiguous duplicate ownership for mixed code PRs and a missing required context for documentation-only PRs. A GitHub “mergeable” result is not proof that the required-check gate passed.

## 5. Current review and implementation sequence

```text
1. obtain fresh independent review on each unchanged final head
2. address findings and rerun exact-head checks after every push
3. repair and verify issue #45 without weakening backend/frontend gates
4. merge PR #38 only after valid approval, resolved threads, and ruleset gates pass
5. verify the new main SHA and checks after merge
6. review/merge #39–#43 only in dependency-safe order with their own gates
7. begin production identity/authentication and authorization next
8. do not begin provider, matching, messaging, financial, or activation work early
```

## 6. Next engineering boundary

After an approved P0 API-foundation merge, the next implementation boundary is production identity/authentication and authorization only:

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
record-policy enforcement
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

This record does not merge a PR, deploy, migrate production data, modify the active ruleset, install Odoo, send externally, or activate any capability.
