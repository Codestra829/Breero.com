from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.errors import DomainError
from app.integrations.geocoding import GeocodingAdapter


def client_with_response(response):
    client = AsyncMock()
    client.get.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = client
    return context


@pytest.mark.asyncio
async def test_geoapify_valid_address(monkeypatch):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"features": [{"properties": {
        "formatted": "Austin, TX 78701", "address_line1": "1 Congress Ave",
        "city": "Austin", "state_code": "TX", "postcode": "78701",
        "country_code": "us", "lat": 30.26, "lon": -97.74,
        "rank": {"confidence": 0.99, "match_type": "full_match"},
        "timezone": {"name": "America/Chicago"},
    }}]}
    with patch("app.integrations.geocoding.httpx.AsyncClient", return_value=client_with_response(response)):
        result = await GeocodingAdapter().geocode("1 Congress Ave")
    assert result.country_code == "US" and result.postal_code == "78701"


@pytest.mark.asyncio
async def test_geoapify_invalid_address(monkeypatch):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"features": []}
    with patch("app.integrations.geocoding.httpx.AsyncClient", return_value=client_with_response(response)):
        with pytest.raises(DomainError, match="Address could not be resolved"):
            await GeocodingAdapter().geocode("not an address")


@pytest.mark.asyncio
async def test_geoapify_provider_failure(monkeypatch):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    client = AsyncMock()
    client.get.side_effect = httpx.ConnectError("unavailable")
    context = AsyncMock()
    context.__aenter__.return_value = client
    with patch("app.integrations.geocoding.httpx.AsyncClient", return_value=context):
        with pytest.raises(DomainError, match="temporarily unavailable"):
            await GeocodingAdapter().geocode("1 Congress Ave")


def response_with_properties(properties):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"features": [{"properties": properties}]}
    return response


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("properties", "error_code"),
    [
        (
            {"country_code": "gb", "postcode": "W1H 1LJ", "lat": 51.5, "lon": -0.16,
             "rank": {"confidence": 0.99}},
            "ADDRESS_OUTSIDE_SERVICE_COUNTRY",
        ),
        (
            {"country_code": "us", "postcode": "787", "lat": 30.2, "lon": -97.7,
             "rank": {"confidence": 0.99}},
            "ADDRESS_ZIP_INVALID",
        ),
        (
            {"country_code": "us", "postcode": "78701", "lat": 30.2, "lon": -97.7,
             "rank": {"confidence": 0.4}},
            "ADDRESS_AMBIGUOUS",
        ),
    ],
)
async def test_geoapify_rejects_unsupported_incomplete_or_ambiguous_results(
    monkeypatch, properties, error_code
):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    with patch(
        "app.integrations.geocoding.httpx.AsyncClient",
        return_value=client_with_response(response_with_properties(properties)),
    ):
        with pytest.raises(DomainError) as exc_info:
            await GeocodingAdapter().geocode("address under test")
    assert exc_info.value.code == error_code


@pytest.mark.asyncio
async def test_geoapify_normalizes_zip_plus_four_to_five_digits(monkeypatch):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    response = response_with_properties({
        "country_code": "us", "postcode": "78701-1234", "lat": 30.2, "lon": -97.7,
        "rank": {"confidence": 0.99},
    })
    with patch("app.integrations.geocoding.httpx.AsyncClient", return_value=client_with_response(response)):
        result = await GeocodingAdapter().geocode("1 Congress Ave")
    assert result.postal_code == "78701"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "error_code"),
    [(401, "GEOCODING_CREDENTIAL_REJECTED"), (429, "GEOCODING_RATE_LIMITED"), (503, "GEOCODING_PROVIDER_FAILURE")],
)
async def test_geoapify_classifies_provider_http_failures(monkeypatch, status_code, error_code):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    request = httpx.Request("GET", "https://api.geoapify.com/v1/geocode/search")
    response = httpx.Response(status_code, request=request)
    mocked = MagicMock()
    mocked.raise_for_status.side_effect = httpx.HTTPStatusError("provider failure", request=request, response=response)
    with patch("app.integrations.geocoding.httpx.AsyncClient", return_value=client_with_response(mocked)):
        with pytest.raises(DomainError) as exc_info:
            await GeocodingAdapter().geocode("address under test")
    assert exc_info.value.code == error_code


@pytest.mark.asyncio
async def test_geoapify_timeout_fails_to_manual_validation(monkeypatch):
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_enabled", True)
    monkeypatch.setattr("app.integrations.geocoding.settings.geocoding_api_key", "file-backed-key")
    client = AsyncMock()
    client.get.side_effect = httpx.ReadTimeout("provider timeout")
    context = AsyncMock()
    context.__aenter__.return_value = client
    with patch("app.integrations.geocoding.httpx.AsyncClient", return_value=context):
        with pytest.raises(DomainError) as exc_info:
            await GeocodingAdapter().geocode("address under test")
    assert exc_info.value.code == "GEOCODING_TIMEOUT"
