# BREERO Angi-Competitive Product Contract

Status: **product target and measurement authority**

BREERO may target a better customer, provider and operator experience than Angi. It must not claim superiority until measurable evidence supports the claim.

Research basis reviewed on 2026-08-27: Angi's official public descriptions of project intake, instant booking/upfront pricing for eligible services, quote comparison, reviews, provider screening language, support/guarantee, professional onboarding and AI project assistance.

This document defines what BREERO must match, where it should differentiate, and how the result is measured.

## 1. Competitive baseline to match

BREERO must eventually provide a coherent version of:

```text
service and project discovery
structured project intake
request-only, quote-required and eligible instant-bookable modes
provider discovery or matching
provider trust/review evidence
quote review and customer decision
clear support and issue-resolution path
provider onboarding and business tooling
mobile-first customer experience
project-scope assistance
```

Matching these features alone does not make BREERO better.

## 2. BREERO differentiation

### A. Full lifecycle transparency

Customer, provider, worker and operator views show the same authoritative progression:

```text
REQUEST
→ ADDRESS / COVERAGE
→ QUOTE OR CAPACITY REVIEW
→ HOLD WHEN APPLICABLE
→ MANUAL DISPATCH
→ PROVIDER ASSIGNMENT
→ SERVICE DELIVERY
→ COMPLETION
→ REVIEW / HISTORY
```

No ambiguous “sent to pros” dead end. Every pending state names the owner and next action.

### B. Specific trust evidence

BREERO shows distinct current facts rather than one generalized badge:

```text
identity
business
license and expiration
insurance and expiration
background screening where applicable
service qualifications
eligible completed-service reviews
```

Expired or pending evidence remains visibly distinct and affects eligibility according to policy.

### C. Capacity-aware marketplace

BREERO treats capacity as a first-class operational domain:

```text
service duration
buffers
travel estimate
existing work
holds
blocks
time off
daily limits
concurrent limits
emergency reserves
```

Availability is never calculated only in the browser and never inferred from a provider profile.

### D. Address, ZIP, service-zone and timezone correctness

BREERO resolves service eligibility through:

```text
normalized address
ZIP and ZIP+4
city/state/county
coordinates
IANA service-address timezone
BREERO service zone
provider coverage
operating-hours and emergency policy
```

This supports accurate nationwide expansion without hardcoded EST/CST/MST/PST logic.

### E. Real dispatch operations

BREERO supports an internal dispatch workspace with candidate eligibility, capacity, travel, compliance, coverage, requested window, timezone and assignment history.

The current release remains manual assignment. Recommendations may assist but do not silently activate automatic assignment.

### F. Provider and worker operating system

Providers receive more than lead notifications:

```text
organization and team management
services and skills
coverage
schedule and exceptions
capacity
credentials and compliance
quotes
jobs
customer relationship after authorization
performance
reviews and messages when enabled
security and support
```

Workers receive an assignment-focused experience separate from provider administration.

### G. One support, trust and dispute layer

BREERO treats support cases, compliance, review moderation, disputes, operational exceptions, integration failures and audit as first-class workflows rather than hidden back-office notes.

### H. Privacy-preserving communication

Customer PII disclosure follows lifecycle purpose. Providers do not receive unrestricted contact, address, conversation or document access before an authorized relationship exists.

### I. Explainable recommendations

Eligibility and scoring remain separated. The operator can understand why a provider is eligible or excluded. Commercial sponsorship cannot override safety, qualification, coverage, schedule, capacity or compliance.

### J. Operational reliability

Every external integration uses:

```text
transactional outbox
durable authenticated inbox
idempotency
claim-token ownership
retry/backoff
terminal failure visibility
manual replay authorization
reconciliation
```

## 3. AI assistance boundary

BREERO may add an AI project assistant in a separate branch after core catalog, request, address, quote, privacy and safety contracts are accepted.

Allowed initial uses:

```text
clarify project description
suggest catalog category
identify missing intake information
summarize customer-provided scope
explain next steps
prepare operator review
```

AI must not authoritatively:

```text
approve a provider
verify compliance
promise a price
create capacity
assign a provider
confirm a booking
make a payment decision
expose private data
```

Every AI result is bounded by deterministic validation and authoritative domain commands.

## 4. Product quality scorecard

BREERO may claim competitive advantage only after measuring the exact released system.

### Customer metrics

```text
request completion rate
time to first qualified response
time to quote
time to assignment
request-to-service conversion
no-capacity rate
cancellation rate
reschedule rate
repeat customer rate
support-contact rate
customer satisfaction
eligible verified-service rating
```

### Provider metrics

```text
application completion
approval cycle time
opportunity response time
acceptance rate
schedule utilization
capacity utilization
completion rate
on-time rate
reassignment rate
provider support burden
provider retention
```

### Operations metrics

```text
unassigned queue age
manual-dispatch handling time
candidate count
coverage misses
compliance blocks
SLA breaches
operational exceptions
outbox/inbox terminal failures
reconciliation discrepancies
```

### Platform metrics

```text
availability latency
booking/request latency
API error rate
database latency
worker heartbeat
queue age
restore RTO/RPO
accessibility defects
mobile journey failures
security incidents
PII leakage events
```

## 5. Launch thresholds

Each release defines targets and guardrails. A future “better than Angi” public claim requires legal/marketing review and durable evidence, not engineering opinion.

Minimum internal product standard:

```text
zero fabricated marketplace state
zero cross-tenant data exposure
zero duplicate authoritative bookings from retry/race tests
zero protected capability activation without approval
zero serious/critical accessibility findings on critical journeys
complete request/quote/booking/assignment history
rehearsed backup and restore
observed worker, queue and integration health
```

## 6. UX acceptance

Every competitive journey must include:

```text
loading
empty
error
restricted
disabled
success
search/filter/sort/pagination where applicable
forms and validation
drawers/dialogs
mobile
keyboard
screen-reader semantics
reduced motion
Chromium/Firefox/WebKit
```

No button may exist without a real action, real route, or explicit unavailable/overview-only explanation.

## 7. Non-goals for current activation

```text
AUTO_ASSIGN_PROVIDER=false
AUTO_CONFIRM_BOOKING=false
PAYMENTS_ENABLED=false
LIVE_PROVIDER_DISPATCH=false
LIVE_EMAIL_DELIVERY=false
LIVE_SMS_DELIVERY=false
MESSAGING_ENABLED=false
REVIEWS_ENABLED=false
FEATURED_PROVIDERS_ENABLED=false
```

Implementation readiness and production activation remain separate changes.

## 8. Current status

```text
COMPETITIVE_TARGET=DEFINED
DESIGN_SYSTEM=PR_67
DASHBOARD_INTERACTIONS=PR_69
IDENTITY_RBAC=PR_68
FULL_MARKETPLACE_IMPLEMENTED=NO
STAGING_CERTIFIED=NO
PRODUCTION_DEPLOYED=NO
PUBLIC_SUPERIORITY_CLAIM=NOT_AUTHORIZED
```
