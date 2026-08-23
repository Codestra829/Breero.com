# BREERO Marketplace V2 UX Design

## Product principle

BREERO is one coherent experience with four purpose-built surfaces:

- breero.com for public discovery and customers;
- partners.breero.com for provider organizations and workers;
- ops.breero.com for dispatch and exception handling;
- admin.breero.com for platform policy, trust, finance and configuration.

The design must communicate the actual runtime capability. A request is not shown as booked, matched, paid or confirmed until the corresponding authoritative state exists.

## Public experience

Primary hero:

What do you need help with?

Problem description, ZIP code and Find qualified professionals action.

The request wizard has eight steps:

1. Service or need
2. Dynamic questions
3. Description
4. Photos and files
5. Address and property
6. Urgency and preferred timing
7. Review
8. Submit

Each step saves a draft, validates accessibly and can resume. Request-only mode clearly states that preferred timing is not an appointment.

## Customer account

Navigation: Requests, Matches, Quotes, Messages, Bookings, Jobs, Reviews, Properties and Profile.

Provider comparison shows approved profile, verified rating, verified jobs, trust badges, distance or coverage statement, response time, quote and availability. Internal matching scores and rejection reasons remain operations-only.

## Provider surface

Navigation: Overview, Opportunities, Leads, Quotes, Messages, Schedule, Jobs, Customers, Workers, Services, Service Areas, Availability, Credentials, Reviews, Analytics, Billing and Settings.

High-risk or unavailable features use an explicit locked/disabled explanation, not a dead button.

## Operations surface

Requests, Matching, Jobs, Providers, Exceptions and Map. Dense queue views support saved filters, age/SLA indicators, ownership, bulk-safe selection and drill-down timelines. Manual commands require reason and confirmation.

## Shared UI

Add ProviderCard, ProviderRating, VerifiedBadge, CredentialBadge, ProjectRequestCard, RequestStatus, OpportunityCard, MatchScore, MatchReason, QuoteCard, QuoteBuilder, QuoteComparison, Conversation, MessageBubble, MessageComposer, JobCard, JobTimeline, AvailabilityPicker, ReviewCard and ServiceAreaMap to packages/ui.

## Quality

- Mobile-first responsive behavior.
- WCAG 2.2 AA targets, keyboard navigation, focus management and screen-reader status announcements.
- Loading, empty, offline, stale, permission-denied and recovery states.
- Plain-language trust and disclosure text.
- No dark patterns for consent, lead purchase, cancellation, subscription or review.
- Component, accessibility, responsive and API contract tests in CI.
