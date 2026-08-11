from dataclasses import dataclass

import httpx

from app.config import settings


@dataclass(frozen=True)
class OdooResult:
    external_id: int


class OdooAdapter:
    """Small JSON-RPC boundary; domain services only publish outbox events."""

    async def execute(
        self, model: str, method: str, args: list, kwargs: dict | None = None
    ) -> object:
        if not all(
            [
                settings.odoo_url,
                settings.odoo_database,
                settings.odoo_username,
                settings.odoo_api_key,
            ]
        ):
            raise RuntimeError("Odoo integration is not configured")
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    settings.odoo_database,
                    settings.odoo_username,
                    settings.odoo_api_key,
                    model,
                    method,
                    args,
                    kwargs or {},
                ],
            },
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{settings.odoo_url.rstrip('/')}/jsonrpc", json=payload)
            response.raise_for_status()
        body = response.json()
        if body.get("error"):
            raise RuntimeError(body["error"].get("message", "Odoo request failed"))
        return body.get("result")
