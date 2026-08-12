# BREERO Odoo CRM architecture

BREERO PostgreSQL is authoritative. Public forms commit a submission and an integration event in one transaction and return `202 REQUEST_ACCEPTED`; they never call Odoo. The worker later sends the versioned envelope to the Odoo 19 `breero_crm` module through JSON-RPC. The module only creates CRM leads, partners, support cases, dispute cases, and sync receipts.

Odoo owns assignment, CRM stages, activities, communication outcomes, and attribution. Booking, job, quote, payment, refund, provider activation, lead-purchase, dispute resolution, earnings, and payouts remain BREERO-owned. Their Odoo fields are read-only mirrors. No card data, credentials, tokens, unrestricted evidence, or precise coordinates are sent.

Supported events are `breero.service_request.created/updated`, `breero.contact_request.created`, `breero.provider_interest.created`, `breero.booking.created/status_changed`, `breero.quote.created/status_changed`, `breero.lead_dispute.created/resolved`, `breero.customer.updated`, and `breero.provider.updated`. Events are emitted only by real domain transitions.
