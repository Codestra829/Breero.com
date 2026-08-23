# BREERO Marketplace V2 Security and RBAC

## Identity authority

The only canonical issuer host is auth.codestra.co. References to auth.codestra.agency must be removed or rejected during implementation.

Use the codestra realm. Human applications use Authorization Code with PKCE S256. Machine clients use Client Credentials. Access tokens are short-lived and validated for issuer, audience, signature, expiry, tenant and required scope.

Expected clients include breero-web, breero-api and breero-provisioner. Provisioning is a protected machine workflow, never a public administrator-creation endpoint.

## Roles

- CUSTOMER
- PROVIDER_OWNER
- PROVIDER_MANAGER
- WORKER
- DISPATCHER
- CUSTOMER_SUPPORT
- TRUST_SAFETY
- FINANCE
- ADMIN
- SUPER_ADMIN

Feature entitlements are separate from roles.

## Permissions

- project_request.read and project_request.manage
- matching.run
- opportunity.read and opportunity.respond
- quote.create, quote.send and quote.accept
- conversation.read and conversation.send
- job.assign, job.execute and job.complete
- credential.verify and provider.suspend
- finance.refund and finance.payout.approve
- admin.feature.manage

Every repository query includes the authorized customer or provider-organization boundary. Hidden buttons are not authorization.

## Data protection

- Minimize customer PII before LeadConnection.
- Store attachment metadata separately and use signed, short-lived downloads.
- Encrypt provider credentials and sensitive documents at rest where supported.
- Hash or tokenize public-source addresses used for abuse controls.
- Never log tokens, contact details, precise coordinates, document content or payment secrets.
- Preserve consent evidence, communication purpose and suppression status separately for email and SMS.
- Transactional consent never implies marketing consent.
- Secrets are mounted from approved secret storage and never committed.

## Required negative tests

- Provider A cannot read Provider B opportunity, quote, conversation, customer PII or job.
- Customer A cannot read Customer B request.
- Worker cannot execute another provider's job.
- Unmatched provider cannot receive customer contact data.
- Dispatcher cannot approve payout.
- Support cannot verify credential.
- Expired credentials and suspended providers cannot match.
- Wrong issuer, audience, tenant, environment, scope, timestamp, nonce or signature fails closed.

## Audit

Record actor, tenant, command, target, reason, prior version, resulting version, correlation ID, source address classification and timestamp. Security, financial, credential, disclosure and manual-override events are immutable.
