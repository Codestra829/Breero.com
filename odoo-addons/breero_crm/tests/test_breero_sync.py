import uuid

from odoo.tests.common import TransactionCase


class TestBreeroSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit = cls.env["call.center.business.unit"].create({
            "name": "BREERO Integration Test", "code": "BREEROTEST",
            "company_id": cls.env.company.id,
        })
        cls.user = cls.env["res.users"].create({"name": "BREERO Integration Test", "login": f"breero-{uuid.uuid4()}@example.test",
            "company_id": cls.env.company.id, "company_ids": [(6, 0, cls.env.company.ids)],
            "call_center_business_unit_ids": [(6, 0, cls.unit.ids)],
            "group_ids": [(6, 0, [cls.env.ref("breero_crm.group_breero_integration").id])]})
        cls.sync = cls.env["breero.sync.event"].with_user(cls.user)

    def envelope(self, event_id=None):
        event_id = event_id or str(uuid.uuid4())
        return {"event_id": event_id, "event_type": "breero.service_request.created", "schema_version": 1,
            "aggregate_id": event_id, "aggregate_version": 1, "occurred_at": "2026-08-12T00:00:00Z",
            "idempotency_key": f"service:{event_id}:1", "source": "breero", "payload": {"submission_id": event_id,
            "route": "SERVICE_REQUEST", "payload": {"name": "Canary Customer", "email": "canary@example.test",
            "service_slug": "plumbing", "city": "Cypress", "source_url": "https://staging.breero.com"}}}

    def test_service_request_and_replay_are_idempotent(self):
        envelope = self.envelope()
        first = self.sync.process_breero_event(envelope)
        second = self.sync.process_breero_event(envelope)
        self.assertEqual(first, second)
        self.assertEqual(self.env["crm.lead"].search_count([("x_breero_request_id", "=", envelope["event_id"])]), 1)

    def test_integration_cannot_delete(self):
        envelope = self.envelope()
        self.sync.process_breero_event(envelope)
        event = self.sync.search([("event_id", "=", envelope["event_id"])])
        with self.assertRaises(Exception):
            event.unlink()
