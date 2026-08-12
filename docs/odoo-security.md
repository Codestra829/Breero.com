# Odoo integration security

The JSON-RPC endpoint must be private/proxy-protected. Secrets belong in the middleware secret store or root-owned `0600` environment file and never in Git, browser configuration, logs, images, or process arguments. The frontend contains no Odoo configuration.

Groups are CRM Agent, CRM Manager, Support Agent, Provider Recruitment, Lead Dispute Reviewer, and Integration Service. The integration group has read/create/write only on required BREERO records and no unlink, settings, module installation, user administration, accounting, company administration, or superuser rights. Record rules separate support, disputes, and provider recruitment.

The module rejects unknown event types, unsupported schemas, non-BREERO sources, idempotency conflicts, and secret/payment-card field names. Normal users see authoritative operational values as read-only mirrors.
