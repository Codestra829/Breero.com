import os
from typing import Any

import httpx
import structlog


class EmailAdapter:
    """Async notification hook with a safe local sink and an external production gateway."""

    def __init__(self) -> None:
        self.delivery_url = os.getenv("EMAIL_DELIVERY_URL", "")
        self.api_key = os.getenv("EMAIL_DELIVERY_API_KEY", "")
        self.environment = os.getenv("APP_ENV", "development")

    async def send(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self.delivery_url:
            if self.environment == "production":
                raise RuntimeError("EMAIL_DELIVERY_URL must be configured in production")
            structlog.get_logger(__name__).info(
                "local_email_delivery", event_type=event_type, recipient=payload.get("email")
            )
            return
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                self.delivery_url,
                json={"event_type": event_type, "payload": payload},
                headers=headers,
            )
        response.raise_for_status()
