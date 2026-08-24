import json
import re
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

EXPECTED_CAPABILITIES = {
    "request_intake": True,
    "instant_booking": False,
    "online_payments": False,
    "automatic_assignment": False,
    "provider_self_service": False,
    "marketplace_matching": False,
    "messaging": False,
    "reviews": False,
}


def test_v2_capabilities_reuse_the_v1_authority() -> None:
    client = TestClient(app)

    v1 = client.get("/api/v1/public/capabilities")
    v2 = client.get("/api/v2/capabilities")

    assert v1.status_code == 200
    assert v2.status_code == 200
    assert v1.json() == EXPECTED_CAPABILITIES
    assert v2.json() == v1.json()


def test_v2_missing_routes_use_the_stable_error_contract() -> None:
    correlation_id = "marketplace-v2-test"
    response = TestClient(app).get(
        "/api/v2/not-implemented",
        headers={"X-Correlation-ID": correlation_id},
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "NOT_FOUND",
        "message": "Not Found",
        "correlation_id": correlation_id,
        "fields": None,
    }
    assert response.headers["x-correlation-id"] == correlation_id
    assert response.headers["x-request-id"]


def test_v1_missing_routes_keep_the_existing_fastapi_contract() -> None:
    response = TestClient(app).get("/api/v1/not-implemented")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_unsafe_trace_headers_are_not_reflected() -> None:
    response = TestClient(app).get(
        "/api/v2/capabilities",
        headers={
            "X-Request-ID": "contains spaces",
            "X-Correlation-ID": "also contains spaces",
        },
    )

    request_id = response.headers["x-request-id"]
    correlation_id = response.headers["x-correlation-id"]
    assert request_id == correlation_id
    assert re.fullmatch(r"[0-9a-f-]{36}", request_id)
    uuid.UUID(request_id)


def test_openapi_exposes_only_the_real_v2_foundation_route() -> None:
    schema = app.openapi()

    assert schema["paths"]["/api/v2/capabilities"]["get"]["operationId"] == (
        "get_v2_capabilities"
    )
    assert "ApiError" in schema["components"]["schemas"]
    assert "/api/v2/project-requests" not in schema["paths"]


def test_checked_in_openapi_matches_the_runtime_v2_contract() -> None:
    api_root = Path(__file__).resolve().parents[1]
    checked_in = json.loads((api_root / "openapi.json").read_text(encoding="utf-8"))
    runtime = app.openapi()

    assert checked_in["info"] == runtime["info"]
    assert checked_in["paths"]["/api/v2/capabilities"] == (
        runtime["paths"]["/api/v2/capabilities"]
    )
    for schema_name in ("ApiError", "PublicCapabilities"):
        assert checked_in["components"]["schemas"][schema_name] == (
            runtime["components"]["schemas"][schema_name]
        )
