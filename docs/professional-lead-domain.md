# Professional opportunity domain

Provider lead operations live under `/api/v1/provider/leads`. Listing and detail are restricted to
an active provider whose declared capabilities include the lead category. Expired, purchased, or
ineligible opportunities are hidden.

Purchase uses an `Idempotency-Key`, locks the opportunity, snapshots server-authoritative price and
currency, creates a canonical `PROFESSIONAL_LEAD` payment intent, rejects key reuse for another lead,
and remains unavailable while Stripe is disabled. The lead is reserved while payment is pending;
signed webhook capture makes the purchase paid, while failure/cancellation releases the reservation. A
purchase is access to a customer opportunity—not a guaranteed job, sale, contract, appointment, or
revenue amount.

Disputes are provider-owned and use a 72-hour deadline from purchase. Accepted submission reasons
are invalid contact, duplicate charged lead, wrong service category, material qualification
mismatch, and documented platform defect. Submission creates an open review; it never automatically
grants a credit or refund. Resolution fields support a later audited credit/refund reference.
Approved Stripe refunds update the linked purchase to refunded; dispute submission alone does not.
