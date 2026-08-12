# Odoo field mapping

Service requests map to `crm.lead` in **BREERO — Customer Service Requests**. Contacts map to `breero.crm.case` in **BREERO — Contact & Support**. Provider interest creates/deduplicates `res.partner` and a recruitment `crm.lead`. Lead disputes map to `breero.crm.case` in **BREERO — Professional Lead Disputes**.

Every record stores the BREERO external reference and event ID. Names, verified contact coordinates, service details, postal address, requested timing, contact preference, source URL, UTM content/term, consent flags, and policy version map to typed fields. UTM source/medium/campaign are reserved for standard Odoo UTM records when configured. Partners match external ID first, then an unambiguous normalized email; names alone never merge.

Operational fields (`x_breero_booking_*`, `job_*`, `quote_*`, `payment_status`, `refund_status`, provider/dispute resolution fields) are read-only. License and insurance self-reporting starts as `provided`, never `verified`.
