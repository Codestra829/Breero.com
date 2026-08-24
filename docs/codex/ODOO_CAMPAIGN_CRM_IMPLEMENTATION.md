# Odoo Campaign CRM — Production Implementation Mission

## Objective

Implement a production-grade campaign CRM in the existing Odoo codebase.

This CRM is a **projection and operational workspace**.

It is not the source of truth for marketplace requests, matching, quotes, bookings, jobs, reviews, payments, or provider eligibility.

The authoritative application remains external to Odoo.

Odoo owns:

```text
Campaign CRM
Agent workspace
Supervisor workspace
Campaign memberships
Agent queues
Activities
Dispositions
Inbox
Sent
Compose
Campaign mailboxes
CRM projections
Campaign reporting
Escalations
Integration inbox/outbox
Integration mappings
Odoo record-level security

```

---

# 1. Git strategy

Create:

```text
crm/odoo-campaign-core
crm/odoo-campaign-security
crm/odoo-agent-workspace
crm/odoo-supervisor-workspace
crm/odoo-mailbox
crm/odoo-integration
crm/odoo-reporting
crm/odoo-provider-recruitment

```

Keep one implementation area per PR.

Recommended merge order:

```text
Campaign Core
    ↓
Security
    ↓
Integration
    ↓
Agent Workspace
    ↓
Mailbox
    ↓
Supervisor Workspace
    ↓
Reporting
    ↓
Provider Recruitment

```

Do not create one large multi-module PR.

---

# 2. Odoo addon structure

Create or normalize:

```text
addons/

breero_crm_core/
breero_campaign/
breero_agent_security/
breero_agent_workspace/
breero_supervisor_workspace/
breero_mailbox/
breero_integration/
breero_compliance/
breero_reporting/
breero_provider_recruitment/

```

Optional later:

```text
breero_callcenter/
breero_support/

```

---

# 3. Standard Odoo modules

Use existing Odoo modules where appropriate:

```text
contacts
crm
mail
calendar

```

Optional:

```text
helpdesk
documents

```

Do not make Odoo Field Service authoritative if the core application already owns Job execution.

---

# 4. Core campaign model

Create:

```text
breero.campaign

```

Fields:

```text
name
code

tenant_id
company_id

campaign_type
status

primary_domain

crm_team_id

supervisor_ids
allowed_agent_ids

start_date
end_date

timezone

email_enabled
sms_enabled
phone_enabled

inbound_enabled
outbound_enabled

safe_mode

max_daily_contacts

external_campaign_id

active

```

Campaign types:

```text
CUSTOMER_ACQUISITION
CUSTOMER_SUPPORT
SERVICE_REQUEST
PROVIDER_RECRUITMENT
PROVIDER_SUPPORT
RETENTION
FOLLOW_UP

```

---

# 5. Tenant model

Create or extend:

```text
breero.tenant

```

Fields:

```text
name
code

company_id

external_tenant_id

active

```

Every campaign-scoped custom record must carry tenant/company context where applicable.

---

# 6. Campaign membership

Create:

```text
breero.campaign.agent

```

Fields:

```text
campaign_id
user_id

agent_role
status

assigned_at
removed_at

daily_limit

mailbox_identity_id

can_compose_email
can_send_sms
can_call
can_reassign
can_export

```

Do not infer campaign access merely from generic CRM team membership.

Campaign membership is the security authority.

---

# 7. Extend CRM lead

Extend:

```text
crm.lead

```

Add:

```text
tenant_id
company_id

campaign_id

external_record_type
external_record_id

external_customer_id
external_provider_id

project_request_id
lead_connection_id
quote_id
booking_id
job_id

source_system

contact_access_level

marketplace_status

integration_status

last_sync_at

assigned_agent_id
supervisor_id

disposition_code
disposition_note

do_not_contact
consent_status

```

External IDs must be indexed where appropriate.

Do not create duplicate CRM leads for the same authoritative record.

---

# 8. CRM state versus authoritative state

CRM stages are local operational workflow.

Recommended stages:

```text
NEW
ASSIGNED
ATTEMPTING_CONTACT
CONTACTED
FOLLOW_UP
QUALIFIED
WAITING_CUSTOMER
WAITING_PROVIDER
ESCALATED
CLOSED_WON
CLOSED_LOST

```

Authoritative marketplace status is a separate read-only projection:

```text
REQUEST_SUBMITTED
MATCHING
MATCHED
QUOTING
BOOKED
JOB_IN_PROGRESS
JOB_COMPLETED

```

Agent may change:

```text
CRM stage
disposition
follow-up
notes
activity

```

Agent may not directly change:

```text
marketplace request state
quote state
booking state
job state
provider eligibility
payment state

```

---

# 9. Contact visibility

Add:

```text
contact_access_level

```

Allowed:

```text
NONE
MASKED
AUTHORIZED

```

Projection behavior:

```text
NONE
→ no direct contact data

MASKED
→ masked email/phone
→ general location only

AUTHORIZED
→ full approved contact information

```

The CRM must never infer authorization.

It receives contact-access state from the authoritative platform.

---

# 10. Security groups

Create:

```text
group_campaign_agent

group_campaign_supervisor

group_campaign_ops

group_campaign_admin

group_campaign_mail_supervisor

group_trust_safety

group_finance

group_integration_operator

```

Do not create one all-powerful Campaign Manager role.

Permissions must be composable.

---

# 11. Agent security

Campaign Agent may:

```text
read/write own assigned leads

read unassigned campaign queue only if campaign policy permits

create/update approved notes

create activities

set approved dispositions

schedule follow-up

read own Inbox/Sent

compose through own campaign mailbox

escalate a record

```

Campaign Agent may not:

```text
read unrelated campaign records

read other tenant records

read another agent's private mailbox

read another agent's private lead by default

see unauthorized customer PII

approve provider credentials

suspend providers

approve refunds

approve payouts

change feature flags

read integration secrets

manage users/roles

```

---

# 12. Supervisor security

Supervisor may:

```text
read all records in supervised campaigns

view agent queues

reassign leads within supervised campaign

view campaign performance

view escalations

review agent activities

acknowledge/resolve campaign operational exceptions

```

Supervisor may not automatically:

```text
access unrelated campaigns

access another tenant

approve finance operations

verify credentials

change system configuration

read integration secrets

read all private mailbox content

```

Mailbox supervision requires separate permission:

```text
campaign.mail.supervise

```

Every supervised mailbox access must be audited.

---

# 13. Ops role

Campaign/Ops Manager may:

```text
operate multiple explicitly assigned campaigns

see queue health

manage escalations

view integration failures

view CRM/customer/provider operational projections

```

Ops does not automatically get:

```text
finance
trust/safety
system admin
secret access

```

---

# 14. Trust & Safety

Trust & Safety may access:

```text
complaints

provider compliance projections

suspension workflows

credential-review projections

disputes

```

Trust & Safety does not automatically get:

```text
campaign send permissions

finance

global system configuration

```

---

# 15. Finance

Finance is separate.

Finance may access:

```text
billing

refund workflows

payout workflows

financial reports

```

Finance should not automatically receive unrelated campaign CRM or mailbox access.

---

# 16. Campaign Admin

Campaign Admin may:

```text
create/edit campaigns

manage campaign membership

manage dispositions

manage mailbox assignments

manage integration mappings

configure campaign limits

```

Campaign Admin does not see raw credentials/secrets in normal screens.

---

# 17. System Admin

System Admin owns:

```text
technical module configuration

system-wide Odoo configuration

security configuration

deployment/module administration

```

Secrets still remain in approved external secret storage.

---

# 18. Record rules

Every campaign-scoped model must have real Odoo record rules.

Do not rely on menu hiding.

Agent CRM lead domain concept:

```text
tenant belongs to agent tenant
AND
campaign belongs to allowed campaigns
AND
record assigned to current agent
OR
record unassigned and campaign permits queue access

```

Supervisor:

```text
tenant allowed
AND
campaign in supervised campaigns

```

Other tenant/campaign records must be invisible.

---

# 19. Model access rules

Implement both:

```text
ir.model.access.csv
+
ir.rule record rules

```

`ir.model.access.csv` determines model capability.

`ir.rule` determines record visibility.

Both are required.

---

# 20. Agent workspace

Build:

```text
My Workspace

```

Dashboard:

```text
My Queue
Inbox
Sent
Compose
Follow-ups
Escalations

```

Summary cards:

```text
New Leads
Follow-ups Today
Overdue
Unread Messages
Escalations

```

Queue columns:

```text
reference
campaign
customer
service
CRM stage
marketplace state
last activity
next action
age

```

---

# 21. Lead workspace

Lead page layout:

```text
HEADER
Reference
Campaign
CRM stage
Marketplace state

LEFT
Customer
Authorized contact
Consent/suppression
Location

RIGHT
Request summary
Provider/match summary
Quote status
Booking/job status

CENTER
Activity timeline

BOTTOM
Notes
Chatter
Compose
Follow-up
Disposition
Escalate

```

Authoritative status fields are read-only.

---

# 22. Dispositions

Create:

```text
breero.disposition

```

Fields:

```text
code
name
campaign_type
active

requires_note
requires_followup
closes_record

suppression_action
escalation_action

```

Examples:

```text
CONTACTED
NO_ANSWER
CALL_BACK
NOT_INTERESTED
DUPLICATE
WRONG_NUMBER
QUALIFIED
BOOKED
ESCALATED
DO_NOT_CONTACT

```

Dispositions can create approved activities/events.

They cannot bypass core-platform policy.

---

# 23. Activities

Use Odoo activities for:

```text
call back

email follow-up

document requested

supervisor review

customer follow-up

provider follow-up

```

Activity state is Odoo-owned.

Marketplace state is not.

---

# 24. Mailbox module

Create:

```text
breero.mailbox.identity
breero.mail.thread
breero.mail.message
breero.mail.delivery

```

Mailbox identity:

```text
tenant_id
campaign_id
user_id

email_address

status

external_provider_identity

created_at
disabled_at

```

Never expose raw SMTP credentials.

---

# 25. Inbox

Agent Inbox shows:

```text
sender

campaign

linked CRM lead

subject

received time

unread

delivery/security status

```

Only messages routed to the agent/campaign are visible.

---

# 26. Sent

Agent Sent shows:

```text
recipient

campaign

CRM lead

subject

sent time

delivery state

```

Delivery state:

```text
PENDING
SENT
DELIVERED
BOUNCED
FAILED
SUPPRESSED

```

---

# 27. Compose

Compose fields:

```text
From

To

Subject

Message

Attachments where approved

```

Before Send validate:

```text
active agent

active campaign membership

mailbox active

recipient authorized

contact access

consent

suppression

campaign send enabled

safe-mode policy

daily limits

rate limits

```

---

# 28. Email routing

Outbound:

```text
Odoo Compose
    ↓
Odoo Outbox
    ↓
Middleware/Control Plane
    ↓
Email Provider

```

Inbound:

```text
Email Provider
    ↓
Policy / malware / tenant validation
    ↓
Middleware
    ↓
Odoo Inbox

```

---

# 29. Supervisor workspace

Build:

```text
Campaign Dashboard
Agent Queues
Assignment/Reassignment
SLA Risk
Escalations
Delivery Health

```

Dashboard metrics:

```text
Active Agents
New Leads
Assigned
Unassigned
Contacted
Follow-ups
Overdue
Escalated
SLA %

```

Agent table:

```text
Agent
Queue
Contacted
Follow-up
Overdue
SLA

```

---

# 30. Reporting

Agent personal metrics:

```text
assigned

contacted

follow-up

closed

response time

SLA

```

Supervisor metrics:

```text
campaign volume

queue size

agent capacity

contact rate

conversion

response time

SLA

escalations

```

Integration metrics:

```text
email delivery

SMS delivery

sync backlog

failed projections

```

---

# 31. Integration mapping

Create:

```text
breero.integration.mapping

```

Fields:

```text
external_system

external_type
external_id

odoo_model
odoo_record_id

tenant_id
campaign_id

external_version

last_sync_at

```

Unique mapping prevents duplicate records.

---

# 32. Integration inbox

Create:

```text
breero.integration.inbox

```

Fields:

```text
provider

external_event_id

event_type

aggregate_type
aggregate_id

schema_version

payload

request_hash

status

received_at
processed_at

error_code

correlation_id

```

Unique:

```text
(provider, external_event_id)

```

---

# 33. Integration outbox

Create:

```text
breero.integration.outbox

```

Fields:

```text
event_type

aggregate_type
aggregate_id

payload

idempotency_key

status

attempt_count
max_attempts

next_attempt_at

lease_owner
lease_until

correlation_id

last_error_code

created_at
delivered_at

```

States:

```text
PENDING_CONFIGURATION
PENDING
PROCESSING
RETRYABLE
DELIVERED
FAILED_TERMINAL

```

---

# 34. Inbound projection flow

```text
Authoritative Platform Event
        ↓
Middleware
        ↓
Authenticated Odoo Endpoint
        ↓
Integration Inbox
        ↓
Worker
        ↓
Mapping Lookup
        ↓
Create/Update Odoo Projection

```

Do not perform long projection work synchronously in callback endpoint.

---

# 35. Outbound command flow

Example agent requests cancellation:

```text
Agent clicks Request Cancellation
        ↓
Odoo local transaction
        ↓
Odoo Outbox command
        ↓
Middleware
        ↓
Authoritative API
        ↓
Domain Command
        ↓
Policy
        ↓
Success/Reject
        ↓
Authoritative event
        ↓
Odoo projection updated

```

Odoo never assumes success before authoritative response/event.

---

# 36. Supported outbound commands

Initially allowlist only commands genuinely needed.

Examples:

```text
request_followup

request_cancellation

support_escalation

customer_contact_attempt

provider_contact_attempt

```

Do not expose generic arbitrary resource mutation.

---

# 37. Odoo webhook/API security

Require:

```text
service authentication

tenant authorization

campaign authorization where applicable

idempotency

correlation ID

request-size limit

content type

timestamp/replay protection for signed callbacks

audit

```

No secrets in payload logs.

---

# 38. PII

Fields should have explicit visibility rules.

Classification:

```text
PUBLIC
INTERNAL
MASKED
SENSITIVE
RESTRICTED

```

Customer phone/email normally:

```text
MASKED

```

until authorized.

Sensitive documents should usually remain in the authoritative platform and be referenced, not replicated into Odoo.

---

# 39. Compliance module

Track projection of:

```text
communication preferences

consent

suppression

do-not-contact

transactional/marketing distinction

```

Campaign action must fail when the relevant channel/purpose is suppressed.

---

# 40. Shared queues

Support:

```text
support@
billing@

```

Routing:

```text
support@
→ support queue

billing@
→ finance queue

```

Do not route `billing@` to ordinary campaign agents.

---

# 41. Disabled agent lifecycle

When agent becomes disabled or loses campaign membership:

```text
campaign access removed

mailbox disabled

new sends denied

queue reassigned according to policy

historical audit retained

```

Do not delete history.

---

# 42. Campaign removal lifecycle

When an agent is removed:

```text
membership = INACTIVE

mailbox disabled

assigned records requeued/reassigned

future messages routed according to fallback policy

```

Historical notes/messages remain.

---

# 43. Integration failure UI

Create an Integration Operations screen.

Show:

```text
event

resource

status

attempts

last error code

next retry

correlation ID

```

Actions:

```text
Retry
Cancel where valid
Open linked record

```

Only:

```text
group_integration_operator

```

or Admin may operate retries.

---

# 44. Negative authorization tests

Mandatory:

```text
Agent A cannot read Agent B private lead

Agent A cannot access Campaign B

Agent A cannot access Tenant B

Agent cannot access unauthorized full PII

Agent cannot read another agent mailbox

Supervisor cannot access unrelated campaign

Supervisor cannot access other tenant

Supervisor cannot approve finance

Supervisor cannot inspect secret configuration

Finance cannot automatically access unrelated CRM

Removed agent cannot read campaign records

Disabled mailbox cannot send

Do-not-contact record cannot be sent through prohibited channel

```

---

# 45. Integration reliability tests

Test:

```text
duplicate inbound event

out-of-order event

stale external version

middleware offline

provider timeout

retry

stale lease

failed terminal

manual retry

mapping conflict

unknown aggregate

unknown campaign

wrong tenant

invalid service identity

```

No duplicate CRM projections.

---

# 46. Module upgrade testing

For every custom Odoo module:

```text
install clean

upgrade from current version

uninstall where safe

record rules

ACLs

views

menus

scheduled actions

integration migrations

```

Run against a disposable Odoo/PostgreSQL environment.

Do not test upgrade on production.

---

# 47. Staging

Deploy Odoo modules to staging first.

Verify:

```text
module upgrade

record rules

campaign membership

agent workspace

supervisor workspace

inbox

sent

compose

projection sync

outbox

inbox

middleware auth

negative authorization

```

Use safe email/SMS recipients only.

---

# 48. Production feature gates

Default:

```text
outbound_email = false

outbound_sms = false

telephony_write = false

automatic_workflow_execution = false

```

Enable independently after certification.

CRM read/projection functionality can be enabled separately from external sends.

---

# 49. Required evidence

Every implementation PR should report:

```text
SOURCE_SHA

MODULES_CHANGED

MIGRATIONS

ODOO_INSTALL_TEST

ODOO_UPGRADE_TEST

ACL_TESTS

RECORD_RULE_TESTS

AGENT_TESTS

SUPERVISOR_TESTS

MAILBOX_TESTS

INTEGRATION_INBOX_TESTS

INTEGRATION_OUTBOX_TESTS

NEGATIVE_AUTH_TESTS

STAGING_STATUS

EXTERNAL_SENDS_ENABLED

BLOCKERS

```

---

# 50. Final Definition of Done

Campaign CRM is production-ready only when:

```text
campaign model complete

campaign membership complete

agent record rules complete

supervisor record rules complete

tenant isolation complete

contact masking complete

CRM projection complete

agent workspace complete

supervisor workspace complete

dispositions complete

activities complete

Inbox complete

Sent complete

Compose complete

mailbox lifecycle complete

Odoo integration inbox complete

Odoo integration outbox complete

integration mappings complete

middleware authentication complete

compliance checks complete

audit complete

integration failure UI complete

negative authorization tests complete

staging upgrade complete

staging agent/supervisor E2E complete

outbound channels remain gated until approved

```

Do not merge or enable external sends merely because module installation succeeds.