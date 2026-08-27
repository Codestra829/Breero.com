import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.domains.auth.models import IdentityLink, User, UserRole
from app.domains.auth.repository import UserRepository
from app.domains.auth.security import decode_access_token

bearer = HTTPBearer(auto_error=False)
BRAND_KEY = "breero"


async def _keycloak_user(
    claims: dict,
    repository: UserRepository,
    session: AsyncSession,
) -> User:
    email = str(claims.get("email") or "").strip().lower()
    subject = str(claims.get("sub") or "").strip()
    issuer = str(claims.get("iss") or "").rstrip("/")
    if not email or not subject or not issuer or not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Verified account required")

    resolved_user: User | None = None
    identity = await repository.identity_by_subject(BRAND_KEY, issuer, subject)
    if identity:
        resolved_user = await repository.by_id(identity.user_id)
    else:
        resolved_user = await repository.by_email(email)
        if not resolved_user:
            raise HTTPException(status_code=403, detail="Account is not provisioned")
        existing = await repository.identity_by_user_issuer(BRAND_KEY, issuer, resolved_user.id)
        if existing:
            raise HTTPException(status_code=403, detail="Identity does not match provisioned account")
        try:
            await repository.add_identity(
                IdentityLink(
                    user_id=resolved_user.id,
                    brand_key=BRAND_KEY,
                    issuer=issuer,
                    subject=subject,
                    email=email,
                )
            )
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            identity = await repository.identity_by_subject(BRAND_KEY, issuer, subject)
            if not identity or identity.user_id != resolved_user.id:
                raise HTTPException(status_code=403, detail="Identity link conflict") from exc

    if not resolved_user:
        raise HTTPException(status_code=401, detail="Invalid or inactive account")

    required_role = {
        UserRole.customer: "breero_customer",
        UserRole.vendor_admin: "breero_provider",
        UserRole.technician: "breero_worker",
        UserRole.operations: "breero_dispatcher",
        UserRole.finance: "breero_support",
        UserRole.admin: "breero_admin",
    }
    token_roles = set((claims.get("realm_access") or {}).get("roles") or [])
    if required_role[resolved_user.role] not in token_roles:
        raise HTTPException(status_code=403, detail="Account role is not authorized")
    return resolved_user


async def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    claims = decode_access_token(credentials.credentials)
    repository = UserRepository(session)
    user: User | None
    if settings.keycloak_enabled:
        user = await _keycloak_user(claims, repository, session)
    else:
        try:
            user_id = uuid.UUID(claims["sub"])
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc
        user = await repository.by_id(user_id)
    if not user or not user.is_active or (
        not settings.keycloak_enabled and claims.get("cv", 1) != user.credential_version
    ):
        raise HTTPException(status_code=401, detail="Invalid or inactive account")
    return user


def require_roles(*roles: UserRole) -> Callable:
    async def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return user

    return dependency
