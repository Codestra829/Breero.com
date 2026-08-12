from dataclasses import dataclass

import httpx

from app.config import settings
from app.core.errors import DomainError


@dataclass(frozen=True)
class GeocodedAddress:
    formatted_address: str
    line1: str
    city: str
    postal_code: str
    country_code: str
    latitude: float
    longitude: float
    provider: str
    provider_reference: str | None = None
    confidence: float | None = None
    quality: str | None = None
    state_code: str | None = None


class FakeGeocodingAdapter:
    def __init__(self, result: GeocodedAddress): self.result = result
    async def geocode(self, address: str) -> GeocodedAddress: return self.result


class GeocodingAdapter:
    async def geocode(self, address: str) -> GeocodedAddress:
        if not settings.geocoding_enabled or not settings.geocoding_api_key:
            raise DomainError(
                "GEOCODING_UNAVAILABLE",
                "Coordinates are required while geocoding is not configured",
                422,
            )
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.geoapify.com/v1/geocode/search",
                params={"text": address, "apiKey": settings.geocoding_api_key, "limit": 1},
            )
            response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            raise DomainError("ADDRESS_NOT_FOUND", "Address could not be resolved", 422)
        props = features[0]["properties"]
        return GeocodedAddress(
            formatted_address=props.get("formatted", address),
            line1=props.get("address_line1", address),
            city=props.get("city", props.get("county", "")),
            state_code=(props.get("state_code") or props.get("state")),
            postal_code=props.get("postcode", ""),
            country_code=props.get("country_code", "").upper(),
            latitude=float(props["lat"]),
            longitude=float(props["lon"]),
            provider="geoapify",
            provider_reference=props.get("place_id"),
            confidence=props.get("rank", {}).get("confidence"),
            quality=props.get("rank", {}).get("match_type"),
        )
