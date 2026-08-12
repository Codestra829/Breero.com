import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.integrations.odoo import OdooAdapter, OdooDeliveryError


def event():
    identifier = uuid.uuid4()
    return SimpleNamespace(id=identifier, event_type="breero.service_request.created",
        aggregate_id=identifier, aggregate_version=1, schema_version=1,
        idempotency_key=f"service:{identifier}:1", created_at=datetime.now(UTC),
        payload={"submission_id": str(identifier), "route": "SERVICE_REQUEST", "payload": {"name": "Canary"}})


def test_typed_event_envelope_contains_stable_identity():
    item = event()
    envelope = OdooAdapter.envelope(item)
    assert envelope["event_id"] == str(item.id)
    assert envelope["idempotency_key"] == item.idempotency_key
    assert envelope["source"] == "breero" and envelope["schema_version"] == 1


@pytest.mark.asyncio
async def test_delivery_requires_typed_ack():
    adapter = OdooAdapter()
    adapter.execute = AsyncMock(return_value={"event_id": str(uuid.uuid4()), "status": "processed",
        "odoo_model": "crm.lead", "odoo_record_id": 42})
    result = await adapter.deliver(event())
    assert result.model == "crm.lead" and result.external_id == 42
    adapter.execute = AsyncMock(return_value={"status": "processed"})
    with pytest.raises(OdooDeliveryError, match="ODOO_INVALID_ACK"):
        await adapter.deliver(event())
