import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.config import settings
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


def configure_odoo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "odoo_url", "https://odoo.example.test/")
    monkeypatch.setattr(settings, "odoo_database", "breero_staging")
    monkeypatch.setattr(settings, "odoo_username", "breero-service")
    monkeypatch.setattr(settings, "odoo_api_key", "test-secret")


def install_transport(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    client_type = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: client_type(transport=transport, **kwargs),
    )


@pytest.mark.asyncio
async def test_execute_fails_closed_without_complete_credentials(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "odoo_url", "https://odoo.example.test")
    monkeypatch.setattr(settings, "odoo_database", "breero_staging")
    monkeypatch.setattr(settings, "odoo_username", "breero-service")
    monkeypatch.setattr(settings, "odoo_api_key", "")

    with pytest.raises(OdooDeliveryError, match="ODOO_NOT_CONFIGURED") as failure:
        await OdooAdapter().execute("breero.sync.event", "integration_health", [])

    assert failure.value.terminal is True


@pytest.mark.asyncio
async def test_execute_uses_authenticated_object_rpc_envelope(monkeypatch: pytest.MonkeyPatch):
    configure_odoo(monkeypatch)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {"status": "ok"}})

    install_transport(monkeypatch, handler)
    result = await OdooAdapter().execute(
        "breero.sync.event", "integration_health", [], {"include_counts": True}
    )

    assert result == {"status": "ok"}
    assert len(requests) == 1
    assert str(requests[0].url) == "https://odoo.example.test/jsonrpc"
    rpc = json.loads(requests[0].content)
    assert rpc["params"]["service"] == "object"
    assert rpc["params"]["method"] == "execute_kw"
    assert rpc["params"]["args"] == [
        "breero_staging",
        "breero-service",
        "test-secret",
        "breero.sync.event",
        "integration_health",
        [],
        {"include_counts": True},
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 403])
async def test_authentication_http_failures_are_terminal(
    monkeypatch: pytest.MonkeyPatch, status: int
):
    configure_odoo(monkeypatch)
    install_transport(monkeypatch, lambda _: httpx.Response(status, json={"error": "denied"}))

    with pytest.raises(OdooDeliveryError, match=f"ODOO_HTTP_{status}") as failure:
        await OdooAdapter().health()

    assert failure.value.terminal is True


@pytest.mark.asyncio
async def test_server_http_failure_remains_retryable(monkeypatch: pytest.MonkeyPatch):
    configure_odoo(monkeypatch)
    install_transport(monkeypatch, lambda _: httpx.Response(503, json={"error": "unavailable"}))

    with pytest.raises(OdooDeliveryError, match="ODOO_HTTP_503") as failure:
        await OdooAdapter().health()

    assert failure.value.terminal is False


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["odoo.exceptions.AccessDenied", "odoo.exceptions.AccessError"])
async def test_rpc_authentication_failures_are_terminal(
    monkeypatch: pytest.MonkeyPatch, name: str
):
    configure_odoo(monkeypatch)
    install_transport(
        monkeypatch,
        lambda _: httpx.Response(
            200,
            json={"error": {"message": "Access denied", "data": {"name": name}}},
        ),
    )

    with pytest.raises(OdooDeliveryError, match="ODOO_AUTH_OR_VALIDATION") as failure:
        await OdooAdapter().health()

    assert failure.value.terminal is True


@pytest.mark.asyncio
async def test_non_authentication_rpc_failure_remains_retryable(monkeypatch: pytest.MonkeyPatch):
    configure_odoo(monkeypatch)
    install_transport(
        monkeypatch,
        lambda _: httpx.Response(
            200,
            json={"error": {"message": "Temporary failure", "data": {"name": "ServerError"}}},
        ),
    )

    with pytest.raises(OdooDeliveryError, match="ODOO_RPC_ERROR") as failure:
        await OdooAdapter().health()

    assert failure.value.terminal is False
