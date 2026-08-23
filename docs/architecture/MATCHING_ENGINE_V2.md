# BREERO Marketplace V2 Matching Engine

## Objective

Matching answers two separate questions:

1. Is the provider eligible for this ProjectRequest?
2. Among eligible providers, how should invitations be ranked?

Hard gates always run before scoring.

## Hard eligibility gates

- provider organization and profile are active;
- provider supports the requested service;
- PostGIS service area covers the verified address;
- required provider and worker credentials are VERIFIED and unexpired;
- insurance is valid where policy requires it;
- provider and worker are not suspended;
- worker skill and legal-entity constraints match;
- availability and effective dates include the requested window;
- capacity remains after holds and assignments;
- runtime capability and marketplace policy permit the action.

Unknown or unavailable evidence fails closed and records a reason.

## Ranking

Default weights are configuration, not code constants:

| Signal | Weight |
|---|---:|
| Availability | 20 |
| Distance or service-area fit | 20 |
| Verified rating | 15 |
| Completion rate | 10 |
| Opportunity acceptance rate | 10 |
| Response speed | 10 |
| Price competitiveness | 5 |
| Existing customer relationship | 5 |
| BREERO quality score | 5 |

A MatchingRun stores algorithm_version, configuration_snapshot, candidate facts, every hard-gate result, score components, final score, rank and rejection reasons. Historical runs are immutable.

## Invitation policy

Start with approximately the top three eligible providers, controlled by runtime policy. Do not reveal full customer PII to all candidates. An accepted Opportunity creates or activates one LeadConnection before contact data or conversation access is granted.

## Concurrency and reproducibility

- Matching reads from one database snapshot.
- Opportunity creation uses unique run/provider constraints.
- Acceptance locks the opportunity and ProjectRequest connection scope.
- Duplicate acceptance produces the original result.
- Expired credentials or capacity changes trigger revalidation at acceptance.
- Holds have explicit expiration and cannot consume capacity after expiry.
- Algorithm version and configuration are deployable, auditable artifacts.

## Operations

The inspector shows candidate, eligibility, reason, distance, credentials, availability, capacity, score components and rank. Manual include/exclude, rerun, withdraw and escalation actions require reason codes and audit events. Operators cannot bypass expired credentials or tenant boundaries.
