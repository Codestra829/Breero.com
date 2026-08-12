import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


ALLOWED_EVENTS = {
    "breero.service_request.created", "breero.service_request.updated",
    "breero.contact_request.created", "breero.provider_interest.created",
    "breero.booking.created", "breero.booking.status_changed",
    "breero.quote.created", "breero.quote.status_changed",
    "breero.lead_dispute.created", "breero.lead_dispute.resolved",
    "breero.customer.updated", "breero.provider.updated",
}
FORBIDDEN_KEYS = {"card_number", "cvc", "password", "access_token", "refresh_token",
                  "stripe_secret", "api_key", "webhook_secret", "private_key"}


class BreeroSyncEvent(models.Model):
    _name = "breero.sync.event"
    _description = "BREERO Sync Event"
    _order = "received_at desc"
    _rec_name = "event_id"

    event_id = fields.Char(required=True, index=True, copy=False)
    event_type = fields.Char(required=True, index=True)
    aggregate_id = fields.Char(required=True, index=True)
    aggregate_version = fields.Integer(required=True)
    idempotency_key = fields.Char(required=True, index=True, copy=False)
    schema_version = fields.Integer(required=True)
    received_at = fields.Datetime(required=True, default=fields.Datetime.now, readonly=True)
    processed_at = fields.Datetime(readonly=True)
    status = fields.Selection([("received", "Received"), ("processed", "Processed"), ("failed", "Failed")], default="received", readonly=True)
    odoo_model = fields.Char(readonly=True)
    odoo_record_id = fields.Integer(readonly=True)
    attempt_count = fields.Integer(default=1, readonly=True)
    last_error_code = fields.Char(readonly=True)
    last_error_at = fields.Datetime(readonly=True)
    payload_digest = fields.Char(readonly=True)

    _event_unique = models.Constraint("UNIQUE(event_id)", "Event already received.")
    _version_unique = models.Constraint("UNIQUE(event_type, aggregate_id, aggregate_version)", "Aggregate version already received.")
    _idempotency_unique = models.Constraint("UNIQUE(idempotency_key)", "Idempotency key already received.")

    @api.model
    def integration_health(self):
        if not self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("Integration service group required")
        return {"status": "ok", "module_version": "19.0.1.0.0", "company": self.env.company.name}

    @api.model
    def process_breero_event(self, envelope):
        if not self.env.user.has_group("breero_crm.group_breero_integration"):
            raise AccessError("Integration service group required")
        required = {"event_id", "event_type", "schema_version", "aggregate_id", "aggregate_version",
                    "occurred_at", "idempotency_key", "source", "payload"}
        if not isinstance(envelope, dict) or required - set(envelope):
            raise ValidationError("Invalid BREERO event envelope")
        if envelope["source"] != "breero" or envelope["schema_version"] != 1:
            raise ValidationError("Unsupported BREERO event source or schema")
        if envelope["event_type"] not in ALLOWED_EVENTS:
            raise ValidationError("Unsupported BREERO event type")
        serialized = json.dumps(envelope["payload"], sort_keys=True, separators=(",", ":"))
        if self._contains_forbidden(envelope["payload"]):
            raise ValidationError("Forbidden secret or payment field")
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        existing = self.search(["|", ("event_id", "=", envelope["event_id"]),
                                ("idempotency_key", "=", envelope["idempotency_key"])], limit=1)
        if existing:
            if existing.payload_digest != digest:
                raise ValidationError("Idempotency payload conflict")
            return existing._ack()
        sync = self.create({"event_id": envelope["event_id"], "event_type": envelope["event_type"],
            "aggregate_id": envelope["aggregate_id"], "aggregate_version": envelope["aggregate_version"],
            "idempotency_key": envelope["idempotency_key"], "schema_version": envelope["schema_version"],
            "payload_digest": digest})
        model, record_id = self._route(envelope, envelope["payload"])
        sync.write({"status": "processed", "processed_at": fields.Datetime.now(),
                    "odoo_model": model, "odoo_record_id": record_id})
        return sync._ack()

    @api.model
    def _contains_forbidden(self, value):
        if isinstance(value, dict):
            return any(str(k).lower() in FORBIDDEN_KEYS or self._contains_forbidden(v) for k, v in value.items())
        if isinstance(value, list):
            return any(self._contains_forbidden(v) for v in value)
        return False

    def _ack(self):
        self.ensure_one()
        return {"event_id": self.event_id, "status": self.status, "odoo_model": self.odoo_model,
                "odoo_record_id": self.odoo_record_id}

    @api.model
    def _team(self, xmlid):
        return self.env.ref(xmlid)

    @api.model
    def _partner(self, payload, provider=False):
        Partner = self.env["res.partner"]
        external_field = "x_breero_provider_id" if provider else "x_breero_customer_id"
        external = payload.get("provider_id") or payload.get("customer_id")
        partner = external and Partner.search([(external_field, "=", external)], limit=1)
        email = str(payload.get("email") or "").strip().lower()
        if not partner and email:
            matches = Partner.search([("email", "=ilike", email)], limit=2)
            partner = matches if len(matches) == 1 else Partner.browse()
        if not partner:
            partner = Partner.create({"name": payload.get("business_name") or payload.get("contact_name") or payload.get("name") or "BREERO Contact",
                "email": email or False, "phone": payload.get("phone") or False,
                "x_breero_contact_type": "provider_company" if provider else "customer",
                external_field: external or False, "x_breero_external_reference": external or False})
        return partner

    @api.model
    def _route(self, envelope, wrapper):
        event_type = envelope["event_type"]
        payload = wrapper.get("payload", wrapper)
        external = wrapper.get("submission_id") or payload.get("dispute_id") or envelope["aggregate_id"]
        if event_type.startswith("breero.contact_request"):
            category = payload.get("category")
            team_xmlid = "breero_crm.team_business" if category == "business" else (
                "breero_crm.team_provider_recruitment" if category == "provider_question" else "breero_crm.team_contact_support")
            team = self._team(team_xmlid)
            case = self.env["breero.crm.case"].search([("case_type", "=", "support"), ("external_reference", "=", external)], limit=1)
            values = {"name": payload.get("subject") or "BREERO Contact", "case_type": "support", "external_reference": external,
                "event_id": envelope["event_id"], "category": category, "message_text": payload.get("message"),
                "source_url": payload.get("source_url"), "team_id": team.id, "partner_id": self._partner(payload).id}
            case = case or self.env["breero.crm.case"].create(values)
            if case: case.write(values)
            return case._name, case.id
        if event_type.startswith("breero.lead_dispute"):
            team = self._team("breero_crm.team_lead_disputes")
            case = self.env["breero.crm.case"].search([("case_type", "=", "lead_dispute"), ("external_reference", "=", external)], limit=1)
            currency = self.env["res.currency"].search([("name", "=", payload.get("currency", "USD"))], limit=1)
            values = {"name": f"BREERO Lead Dispute — {external}", "case_type": "lead_dispute", "external_reference": external,
                "event_id": envelope["event_id"], "team_id": team.id, "partner_id": self._partner(payload, True).id,
                "lead_id": payload.get("lead_id"), "dispute_id": payload.get("dispute_id"), "provider_id": payload.get("provider_id"),
                "dispute_reason": payload.get("reason"), "dispute_submitted_at": payload.get("submitted_at"),
                "dispute_deadline_at": payload.get("deadline_at"), "dispute_status": payload.get("status"),
                "disputed_amount": (payload.get("amount_minor") or 0) / 100, "currency_id": currency.id or False,
                "backend_authority_url_or_id": payload.get("purchase_id")}
            case = case or self.env["breero.crm.case"].create(values)
            if case: case.write(values)
            return case._name, case.id
        provider = event_type.startswith("breero.provider_interest")
        team = self._team("breero_crm.team_provider_recruitment" if provider else "breero_crm.team_customer_requests")
        lead = self.env["crm.lead"].search([("x_breero_request_id", "=", external)], limit=1)
        partner = self._partner(payload, provider)
        record_type = "provider_interest" if provider else "service_request"
        values = {"name": f"[BREERO] {payload.get('service_name') or payload.get('service_slug') or record_type.replace('_', ' ').title()} — {payload.get('contact_name') or payload.get('name') or partner.name} — {payload.get('city') or ''}",
            "type": "lead", "team_id": team.id, "partner_id": partner.id, "contact_name": payload.get("contact_name") or payload.get("name"),
            "partner_name": payload.get("business_name"), "email_from": payload.get("email"), "phone": payload.get("phone"),
            "street": payload.get("address_line1"), "city": payload.get("city"), "zip": payload.get("postal_code"),
            "x_breero_request_id": external, "x_breero_external_reference": external, "x_breero_event_id": envelope["event_id"],
            "x_breero_record_type": record_type, "x_breero_schema_version": envelope["schema_version"],
            "x_breero_last_synced_at": fields.Datetime.now(), "x_breero_sync_status": "delivered",
            "x_breero_service_id": payload.get("service_id"), "x_breero_service_slug": payload.get("service_slug"),
            "x_breero_request_details": payload.get("service_description"), "x_breero_requested_date": payload.get("requested_date"),
            "x_breero_requested_time_window": payload.get("requested_timing"), "x_breero_contact_preference": payload.get("contact_preference"),
            "x_breero_source_url": payload.get("source_url"), "x_breero_utm_content": payload.get("utm_content"), "x_breero_utm_term": payload.get("utm_term"),
            "x_breero_transactional_contact_allowed": payload.get("transactional_contact_allowed", True),
            "x_breero_marketing_consent": payload.get("marketing_consent", False), "x_breero_sms_consent": payload.get("sms_consent", False),
            "x_breero_email_consent": payload.get("email_consent", False), "x_breero_policy_version": payload.get("policy_version")}
        if provider:
            values.update({"x_breero_provider_interest_id": external,
                "x_breero_business_name": payload.get("business_name"), "x_breero_website": payload.get("business_website"),
                "x_breero_service_categories": ", ".join(payload.get("service_categories") or []),
                "x_breero_service_area_text": ", ".join(x for x in (payload.get("city"), payload.get("state"), payload.get("postal_code")) if x),
                "x_breero_license_information": payload.get("license_details"), "x_breero_provider_notes": payload.get("notes")})
        lead = lead or self.env["crm.lead"].create(values)
        if lead: lead.write(values)
        return lead._name, lead.id
