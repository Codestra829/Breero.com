import hashlib
import hmac
import json
import time

import pytest

from app.domains.payments.exceptions import InvalidWebhook
from app.integrations.stripe import StripeAdapter


def sign(body: bytes, secret: str, timestamp: int) -> str:
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_verifies_valid_webhook() -> None:
    body = json.dumps({"id": "evt_1", "type": "payment_intent.succeeded"}).encode()
    now = int(time.time())
    adapter = StripeAdapter("sk_test", "whsec_test")

    assert adapter.verify_webhook(body, sign(body, "whsec_test", now))["id"] == "evt_1"


def test_rejects_tampered_webhook() -> None:
    body = b'{"id":"evt_1","type":"payment_intent.succeeded"}'
    adapter = StripeAdapter("sk_test", "whsec_test")

    with pytest.raises(InvalidWebhook, match="verification failed"):
        adapter.verify_webhook(body + b" ", sign(body, "whsec_test", int(time.time())))


def test_rejects_stale_webhook() -> None:
    body = b'{"id":"evt_1","type":"payment_intent.succeeded"}'
    adapter = StripeAdapter("sk_test", "whsec_test", webhook_tolerance_seconds=10)

    with pytest.raises(InvalidWebhook, match="outside tolerance"):
        adapter.verify_webhook(body, sign(body, "whsec_test", int(time.time()) - 20))
