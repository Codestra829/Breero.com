from odoo import fields, models
from odoo.exceptions import AccessError


class BreeroCrmCase(models.Model):
    _name = "breero.crm.case"
    _description = "BREERO CRM Case"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True)
    case_type = fields.Selection([("support", "Support"), ("lead_dispute", "Lead Dispute")], required=True, index=True)
    external_reference = fields.Char(required=True, index=True, copy=False)
    event_id = fields.Char(index=True, copy=False)
    stage = fields.Selection([(x, x.replace("_", " ").title()) for x in (
        "new", "assigned", "customer_contacted", "waiting_customer", "waiting_internal", "under_review", "resolved", "closed")], default="new", tracking=True)
    category = fields.Char(index=True)
    partner_id = fields.Many2one("res.partner")
    team_id = fields.Many2one("crm.team", required=True)
    user_id = fields.Many2one("res.users")
    message_text = fields.Text()
    source_url = fields.Char()
    contact_preference = fields.Char()
    lead_id = fields.Char(readonly=True)
    dispute_id = fields.Char(readonly=True, index=True)
    provider_id = fields.Char(readonly=True)
    dispute_reason = fields.Char(readonly=True)
    dispute_submitted_at = fields.Datetime(readonly=True)
    dispute_deadline_at = fields.Datetime(readonly=True)
    dispute_status = fields.Char(readonly=True)
    disputed_amount = fields.Monetary(readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    resolution_type = fields.Char(readonly=True)
    resolution_reference = fields.Char(readonly=True)
    backend_authority_url_or_id = fields.Char(readonly=True)

    _external_unique = models.Constraint("UNIQUE(case_type, external_reference)", "BREERO case already exists.")

    def write(self, vals):
        mirrors = {"lead_id", "dispute_id", "provider_id", "dispute_reason", "dispute_submitted_at",
            "dispute_deadline_at", "dispute_status", "disputed_amount", "currency_id",
            "resolution_type", "resolution_reference", "backend_authority_url_or_id"}
        if mirrors.intersection(vals) and not self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("BREERO dispute authority fields are read-only")
        return super().write(vals)
