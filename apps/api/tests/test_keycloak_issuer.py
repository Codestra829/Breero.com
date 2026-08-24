import pytest
from fastapi import HTTPException

from app.config import settings
from app.domains.auth.security import (
    CANONICAL_KEYCLOAK_ISSUER,
    _validated_keycloak_issuer,
)


def test_canonical_keycloak_issuer_is_accepted(monkeypatch) -> None:
    monkeypatch.setattr(settings, "keycloak_issuer", CANONICAL_KEYCLOAK_ISSUER)
    assert _validated_keycloak_issuer() == CANONICAL_KEYCLOAK_ISSUER


def test_legacy_keycloak_issuer_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "keycloak_issuer",
        "https://auth.codestra.agency/realms/codestra",
    )
    with pytest.raises(HTTPException) as exc:
        _validated_keycloak_issuer()
    assert exc.value.status_code == 401
