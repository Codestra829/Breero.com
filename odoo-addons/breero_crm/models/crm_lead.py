from odoo import fields, models
from odoo.exceptions import AccessError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    x_breero_request_id = fields.Char(index=True, copy=False)
    x_breero_event_id = fields.Char(index=True, copy=False)
    x_breero_external_reference = fields.Char(index=True, copy=False)
    x_breero_record_type = fields.Selection([(x, x.replace("_", " ").title()) for x in (
        "service_request", "contact_request", "provider_interest", "booking_followup", "lead_dispute", "business_enquiry")])
    x_breero_schema_version = fields.Integer(readonly=True)
    x_breero_created_at = fields.Datetime(readonly=True)
    x_breero_last_synced_at = fields.Datetime(readonly=True)
    x_breero_sync_status = fields.Selection([("delivered", "Delivered"), ("possible_duplicate", "Possible duplicate"), ("failed", "Failed")], readonly=True)
    x_breero_sync_error_code = fields.Char(readonly=True)
    x_breero_customer_id = fields.Char(index=True, copy=False)
    x_breero_contact_preference = fields.Selection([("email", "Email"), ("phone", "Phone"), ("text", "Text")])
    x_breero_language = fields.Char()
    x_breero_customer_timezone = fields.Char()
    x_breero_service_id = fields.Char()
    x_breero_service_slug = fields.Char()
    x_breero_service_name = fields.Char()
    x_breero_service_category = fields.Char()
    x_breero_request_details = fields.Text()
    x_breero_requested_date = fields.Date()
    x_breero_requested_time_window = fields.Char()
    x_breero_normalized_address = fields.Char()
    x_breero_serviceability_status = fields.Char(readonly=True)
    x_breero_utm_content = fields.Char()
    x_breero_utm_term = fields.Char()
    x_breero_source_url = fields.Char()
    x_breero_referrer = fields.Char()
    x_breero_landing_page = fields.Char()
    x_breero_transactional_contact_allowed = fields.Boolean(default=True)
    x_breero_marketing_consent = fields.Boolean(default=False)
    x_breero_sms_consent = fields.Boolean(default=False)
    x_breero_email_consent = fields.Boolean(default=False)
    x_breero_consent_timestamp = fields.Datetime()
    x_breero_consent_source = fields.Char()
    x_breero_policy_version = fields.Char()
    x_breero_do_not_call = fields.Boolean()
    x_breero_do_not_sms = fields.Boolean()
    x_breero_do_not_email = fields.Boolean()
    x_breero_booking_id = fields.Char(readonly=True)
    x_breero_booking_status = fields.Char(readonly=True)
    x_breero_job_id = fields.Char(readonly=True)
    x_breero_job_status = fields.Char(readonly=True)
    x_breero_provider_id = fields.Char(readonly=True)
    x_breero_provider_name = fields.Char(readonly=True)
    x_breero_quote_id = fields.Char(readonly=True)
    x_breero_quote_status = fields.Char(readonly=True)
    x_breero_payment_status = fields.Char(readonly=True)
    x_breero_refund_status = fields.Char(readonly=True)
    x_breero_provider_interest_id = fields.Char(index=True)
    x_breero_business_name = fields.Char()
    x_breero_website = fields.Char()
    x_breero_service_categories = fields.Char()
    x_breero_service_area_text = fields.Char()
    x_breero_license_information = fields.Text()
    x_breero_insurance_information = fields.Text()
    x_breero_years_experience = fields.Integer()
    x_breero_team_size = fields.Integer()
    x_breero_provider_notes = fields.Text()
    x_breero_contact_request_id = fields.Char(index=True)
    x_breero_contact_category = fields.Char()
    x_breero_subject = fields.Char()
    x_breero_message = fields.Text()
    x_breero_booking_reference = fields.Char()
    x_breero_service_reference = fields.Char()
    x_breero_support_priority = fields.Selection([("normal", "Normal"), ("urgent", "Urgent")], default="normal")

    _breero_request_unique = models.Constraint("UNIQUE(x_breero_request_id)", "BREERO request already exists.")

    def write(self, vals):
        mirrors = {"x_breero_serviceability_status", "x_breero_booking_id", "x_breero_booking_status",
            "x_breero_job_id", "x_breero_job_status", "x_breero_provider_id", "x_breero_provider_name",
            "x_breero_quote_id", "x_breero_quote_status", "x_breero_payment_status", "x_breero_refund_status"}
        if mirrors.intersection(vals) and not self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("BREERO authoritative mirror fields are read-only")
        return super().write(vals)

    def unlink(self):
        if self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("BREERO integration service cannot delete records")
        return super().unlink()
