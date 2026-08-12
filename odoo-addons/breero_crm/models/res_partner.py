from odoo import fields, models
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_breero_contact_type = fields.Selection([(x, x.replace("_", " ").title()) for x in (
        "customer", "provider_company", "provider_contact", "provider_worker", "business_contact")])
    x_breero_customer_id = fields.Char(index=True, copy=False)
    x_breero_provider_id = fields.Char(index=True, copy=False)
    x_breero_provider_status = fields.Char(readonly=True)
    x_breero_service_categories = fields.Char()
    x_breero_service_areas = fields.Char()
    x_breero_license_status = fields.Selection([(x, x.replace("_", " ").title()) for x in (
        "provided", "under_review", "verified", "expired", "rejected", "not_required")], default="provided")
    x_breero_insurance_status = fields.Selection([(x, x.replace("_", " ").title()) for x in (
        "provided", "under_review", "verified", "expired", "rejected", "not_required")], default="provided")
    x_breero_last_synced_at = fields.Datetime(readonly=True)
    x_breero_external_reference = fields.Char(index=True, copy=False)

    def write(self, vals):
        if "x_breero_provider_status" in vals and not self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("BREERO provider status is read-only")
        return super().write(vals)

    def unlink(self):
        if self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("BREERO integration service cannot delete records")
        return super().unlink()
