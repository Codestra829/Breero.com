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
