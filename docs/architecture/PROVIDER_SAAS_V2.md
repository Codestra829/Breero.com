# BREERO Marketplace V2 Provider SaaS

## Purpose

The partner product serves both BREERO marketplace work and provider-direct operations without mixing attribution or tenant data.

## Tenancy

A ProviderOrganization owns memberships, workers, services, service areas, schedules, credentials, documents, conversations, quotes, customers, jobs and entitlements. Every provider-owned row carries organization_id. A user may belong to more than one organization and must select an explicit active organization.

## Onboarding

1. Create or accept provider organization invitation.
2. Complete legal profile and contact details.
3. Declare services and jurisdictions.
4. Configure service areas using postal codes, radius or polygons.
5. Add workers and skills.
6. Submit requirement-driven credentials and insurance.
7. Configure availability, exceptions and capacity.
8. Pass review before marketplace activation.

Approval in Odoo never activates a provider. Activation is a BREERO command with evidence and audit.

## Product areas

- Overview: opportunities, quotes, jobs today, response/completion rate and credential warnings.
- Opportunities and Leads: controlled marketplace disclosure and response.
- Quotes: versioned builder, line items, delivery and decision state.
- Messages: participant-scoped customer communication.
- Schedule: rules, exceptions, capacity and worker views.
- Jobs: assignments, commands, evidence and completion.
- Customers: marketplace and direct CRM with attribution.
- Trust: credentials, reviews and performance.
- Analytics: funnel, response, conversion, completion and retention.
- Billing: future subscription and lead/transaction history, capability-gated.

## Attribution

Every customer relationship and job records BREERO_MARKETPLACE, PROVIDER_DIRECT, REFERRAL or OTHER. Provider-direct records never gain a verified BREERO marketplace review unless they meet the verified-job policy.

## Entitlements

Entitlements are server-owned and independent of RBAC. Future FREE, PRO and BUSINESS plans may gate CRM, quotes, scheduling, analytics, profile priority, lead limits, team seats and automation. Disabling an entitlement blocks the backend command as well as the UI.

## Marketplace quality

Response time, completion, cancellation, dispute and verified-review metrics are reproducible projections from authoritative events. Providers cannot directly edit them. Credential expiry or suspension immediately removes matching eligibility.
