from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status

from app.api.v1 import auth


@pytest.mark.asyncio
async def test_public_registration_is_disabled_when_keycloak_is_enabled(monkeypatch) -> None:
    monkeypatch.setattr(auth, "settings", SimpleNamespace(keycloak_enabled=True))

    with pytest.raises(HTTPException) as exc_info:
        await auth.register(None, None, None, None)  # type: ignore[arg-type]

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Public account registration is disabled"
