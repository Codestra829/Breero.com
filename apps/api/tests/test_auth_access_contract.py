import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.api.v1 import auth
from app.domains.auth.access_service import DASHBOARD_BY_ROLE, DEFAULT_ACCESS, DEFAULT_PERMISSIONS
from app.domains.auth.models import AccessRole, Department, TenantScope, UserRole
from app.domains.auth.schemas import AccessAssignmentInput, AccessProfileUpdate


def test_every_coarse_user_role_has_default_portal_access() -> None:
    assert set(DEFAULT_ACCESS) == set(UserRole)
    for role, (access_role, department, scope) in DEFAULT_ACCESS.items():
        assert access_role in AccessRole
        assert department in Department
        assert scope in TenantScope
        assert DASHBOARD_BY_ROLE[access_role].startswith("/")
        assert DEFAULT_PERMISSIONS[access_role]
        assert role.value


def test_every_department_role_has_a_dashboard_and_permission_profile() -> None:
    assert set(DASHBOARD_BY_ROLE) == set(AccessRole)
    assert set(DEFAULT_PERMISSIONS) == set(AccessRole)


def test_vendor_scope_requires_vendor_id() -> None:
    with pytest.raises(ValidationError):
        AccessAssignmentInput(
            role=AccessRole.vendor_admin,
            department=Department.provider,
            tenant_scope=TenantScope.vendor,
        )


def test_non_vendor_scope_rejects_vendor_id() -> None:
    with pytest.raises(ValidationError):
        AccessAssignmentInput(
            role=AccessRole.operations,
            department=Department.dispatch,
            tenant_scope=TenantScope.brand,
            vendor_id=uuid.uuid4(),
        )


def test_access_profile_allows_only_one_primary_assignment() -> None:
    with pytest.raises(ValidationError):
        AccessProfileUpdate(
            assignments=[
                AccessAssignmentInput(
                    role=AccessRole.operations,
                    department=Department.dispatch,
                    is_primary=True,
                ),
                AccessAssignmentInput(
                    role=AccessRole.support,
                    department=Department.customer_support,
                    is_primary=True,
                ),
            ]
        )


def test_access_profile_rejects_duplicate_role_department() -> None:
    with pytest.raises(ValidationError):
        AccessProfileUpdate(
            assignments=[
                AccessAssignmentInput(
                    role=AccessRole.quality,
                    department=Department.quality,
                ),
                AccessAssignmentInput(
                    role=AccessRole.quality,
                    department=Department.quality,
                ),
            ]
        )


def test_local_credentials_are_disabled_when_keycloak_is_authoritative(monkeypatch) -> None:
    monkeypatch.setattr(auth, "settings", SimpleNamespace(keycloak_enabled=True))
    with pytest.raises(HTTPException) as exc_info:
        auth.local_auth_only()
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "identity provider" in str(exc_info.value.detail)
