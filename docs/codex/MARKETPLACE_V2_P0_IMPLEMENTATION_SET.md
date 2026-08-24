# BREERO Marketplace V2 — P0 Production Foundation Implementation Set

Yes. I would add the following **missing production foundation code** to the existing BREERO monorepo before expanding the marketplace features. This keeps the current backend/frontend separation and gives the feature branches a common production-grade base.

I would treat this as the implementation package for:

```text
be/marketplace-v2-p0-api-foundation
be/marketplace-v2-p0-authentication
be/marketplace-v2-p0-authorization
be/marketplace-v2-p0-capabilities-idempotency
be/marketplace-v2-p0-integration-reliability
be/marketplace-v2-p0-storage-uploads
be/marketplace-v2-p0-operations-foundation
```

I am intentionally **not claiming this code is CI-green until it is merged into the actual repo and run against its exact models/migrations**, because some imports/model names must align with the current BREERO codebase.

# 1. Files to add

```text
apps/api/app/

├── api/
│   └── v2/
│       ├── __init__.py
│       ├── router.py
│       ├── public.py
│       ├── uploads.py
│       └── integrations.py
│
├── domains/
│   ├── authorization/
│   │   ├── __init__.py
│   │   ├── principal.py
│   │   ├── permissions.py
│   │   ├── policies.py
│   │   └── dependencies.py
│   │
│   ├── common/
│   │   ├── command_context.py
│   │   ├── domain_event.py
│   │   ├── idempotency.py
│   │   ├── audit.py
│   │   ├── exceptions.py
│   │   └── state_machine.py
│   │
│   ├── capabilities/
│   │   ├── registry.py
│   │   └── dependencies.py
│   │
│   ├── integrations/
│   │   ├── inbox.py
│   │   └── adapters.py
│   │
│   └── storage/
│       ├── models.py
│       ├── schemas.py
│       ├── service.py
│       └── providers.py
│
├── integrations/
│   ├── base.py
│   ├── codestra.py
│   ├── klyrow.py
│   ├── telnexa.py
│   ├── odoo.py
│   ├── n8n.py
│   ├── stripe.py
│   ├── geocoder.py
│   ├── object_storage.py
│   └── malware.py
│
├── workers/
│   ├── outbox.py
│   ├── inbox.py
│   ├── scheduler.py
│   └── scanner.py
│
└── observability/
    ├── logging.py
    ├── metrics.py
    └── middleware.py
```

And:

```text
apps/api/tests/
├── authorization/
├── idempotency/
├── integrations/
├── storage/
├── concurrency/
└── api_v2/
```

---

# 2. Principal

`apps/api/app/domains/authorization/principal.py`

```python
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Principal:
    user_id: UUID

    issuer: str
    subject: str

    roles: frozenset[str]
    permissions: frozenset[str]

    provider_ids: frozenset[UUID]

    worker_id: UUID | None

    tenant_id: UUID | None
    legal_entity_ids: frozenset[UUID]

    @property
    def identity_key(self) -> str:
        return f"{self.issuer}|{self.subject}"

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
```

---

# 3. Permissions

`apps/api/app/domains/authorization/permissions.py`

```python
PROJECT_REQUEST_READ = "project_request.read"
PROJECT_REQUEST_MANAGE = "project_request.manage"

MATCHING_RUN = "matching.run"
MATCHING_INSPECT = "matching.inspect"

OPPORTUNITY_READ = "opportunity.read"
OPPORTUNITY_RESPOND = "opportunity.respond"
OPPORTUNITY_MANAGE = "opportunity.manage"

QUOTE_READ = "quote.read"
QUOTE_CREATE = "quote.create"
QUOTE_SEND = "quote.send"
QUOTE_ACCEPT = "quote.accept"

CONVERSATION_READ = "conversation.read"
CONVERSATION_SEND = "conversation.send"

BOOKING_READ = "booking.read"
BOOKING_MANAGE = "booking.manage"

JOB_READ = "job.read"
JOB_ASSIGN = "job.assign"
JOB_EXECUTE = "job.execute"
JOB_COMPLETE = "job.complete"

PROVIDER_READ = "provider.read"
PROVIDER_MANAGE = "provider.manage"

CREDENTIAL_MANAGE = "provider.credentials.manage"
CREDENTIAL_VERIFY = "provider.credentials.verify"

PROVIDER_SUSPEND = "provider.suspend"

REVIEW_CREATE = "review.create"
REVIEW_RESPOND = "review.respond"
REVIEW_MODERATE = "review.moderate"

INTEGRATION_READ = "integration.read"
INTEGRATION_RETRY = "integration.retry"

FINANCE_REFUND = "finance.refund"
FINANCE_PAYOUT_APPROVE = "finance.payout.approve"

ADMIN_USERS = "admin.users.manage"
ADMIN_FEATURES = "admin.features.manage"
ADMIN_AUDIT = "admin.audit.read"
```

---

# 4. Permission dependency

`apps/api/app/domains/authorization/dependencies.py`

```python
from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.domains.authorization.principal import Principal
from app.domains.auth.dependencies import current_principal


def require_permission(permission: str) -> Callable:
    async def dependency(
        principal: Principal = Depends(current_principal),
    ) -> Principal:
        if not principal.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "permission": permission,
                },
            )

        return principal

    return dependency
```

Adjust the import to whatever function eventually resolves the new `Principal`.

---

# 5. Record policy helpers

`apps/api/app/domains/authorization/policies.py`

```python
from uuid import UUID

from app.core.errors import DomainError
from app.domains.authorization.principal import Principal


class AuthorizationPolicy:
    @staticmethod
    def require_customer(
        *,
        resource_customer_id: UUID,
        principal: Principal,
    ) -> None:
        if resource_customer_id != principal.user_id:
            raise DomainError(
                "RESOURCE_NOT_ACCESSIBLE",
                "The requested resource is not available.",
                404,
            )

    @staticmethod
    def require_provider(
        *,
        provider_id: UUID,
        principal: Principal,
    ) -> None:
        if provider_id not in principal.provider_ids:
            raise DomainError(
                "RESOURCE_NOT_ACCESSIBLE",
                "The requested resource is not available.",
                404,
            )

    @staticmethod
    def require_worker(
        *,
        worker_id: UUID,
        principal: Principal,
    ) -> None:
        if principal.worker_id != worker_id:
            raise DomainError(
                "RESOURCE_NOT_ACCESSIBLE",
                "The requested resource is not available.",
                404,
            )
```

For cross-tenant resources I prefer `404` rather than revealing that another tenant's resource exists.

---

# 6. Command context

`apps/api/app/domains/common/command_context.py`

```python
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CommandContext:
    actor_id: UUID | None

    request_id: str
    correlation_id: str

    tenant_id: UUID | None = None
    legal_entity_id: UUID | None = None

    idempotency_key: str | None = None

    ip_address: str | None = None
    user_agent: str | None = None
```

---

# 7. Domain event

`apps/api/app/domains/common/domain_event.py`

```python
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_type: str

    aggregate_type: str
    aggregate_id: UUID
    aggregate_version: int

    payload: dict[str, Any]

    correlation_id: str

    schema_version: int = 1

    tenant_id: UUID | None = None
    legal_entity_id: UUID | None = None

    causation_id: str | None = None

    event_id: UUID = uuid4()
    occurred_at: datetime = datetime.now(UTC)

    def envelope(self) -> dict:
        data = asdict(self)

        data["event_id"] = str(self.event_id)
        data["aggregate_id"] = str(self.aggregate_id)
        data["occurred_at"] = self.occurred_at.isoformat()

        if self.tenant_id:
            data["tenant_id"] = str(self.tenant_id)

        if self.legal_entity_id:
            data["legal_entity_id"] = str(self.legal_entity_id)

        return data
```

For mutable-default safety, the write-enabled implementation agent should convert timestamps/UUID defaults to `field(default_factory=...)`.

Correct production version:

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    aggregate_version: int
    payload: dict
    correlation_id: str

    schema_version: int = 1

    tenant_id: UUID | None = None
    legal_entity_id: UUID | None = None

    causation_id: str | None = None

    event_id: UUID = field(default_factory=uuid4)

    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
```

Use the second version.

---

# 8. Generic state machine

`apps/api/app/domains/common/state_machine.py`

```python
from collections.abc import Mapping
from typing import Generic, TypeVar

from app.core.errors import DomainError


State = TypeVar("State", bound=str)


class StateMachine(Generic[State]):
    def __init__(
        self,
        transitions: Mapping[State, set[State]],
    ):
        self.transitions = transitions

    def can_transition(
        self,
        current: State,
        target: State,
    ) -> bool:
        return target in self.transitions.get(
            current,
            set(),
        )

    def require_transition(
        self,
        current: State,
        target: State,
    ) -> None:
        if not self.can_transition(current, target):
            raise DomainError(
                "INVALID_STATE_TRANSITION",
                f"Cannot transition from {current} to {target}.",
                409,
            )
```

Each domain owns its own transition map.

---

# 9. Idempotency model

Add via Alembic and SQLAlchemy:

```python
class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    actor_key = mapped_column(
        String(512),
        nullable=False,
    )

    operation = mapped_column(
        String(160),
        nullable=False,
    )

    idempotency_key = mapped_column(
        String(255),
        nullable=False,
    )

    request_hash = mapped_column(
        String(64),
        nullable=False,
    )

    status = mapped_column(
        String(32),
        nullable=False,
    )

    resource_type = mapped_column(
        String(100),
        nullable=True,
    )

    resource_id = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    response_code = mapped_column(
        Integer,
        nullable=True,
    )

    response_json = mapped_column(
        JSONB,
        nullable=True,
    )

    expires_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "actor_key",
            "operation",
            "idempotency_key",
            name="uq_idempotency_actor_operation_key",
        ),
    )
```

---

# 10. Idempotency service

`apps/api/app/domains/common/idempotency.py`

```python
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.common.models import IdempotencyRecord


def canonical_hash(payload: dict) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class IdempotencyAcquireResult:
    replay: bool
    record: IdempotencyRecord


class IdempotencyService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def acquire(
        self,
        *,
        actor_key: str,
        operation: str,
        key: str,
        payload: dict,
        ttl_hours: int = 24,
    ) -> IdempotencyAcquireResult:
        request_hash = canonical_hash(payload)

        record = await self.session.scalar(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.actor_key
                == actor_key,
                IdempotencyRecord.operation
                == operation,
                IdempotencyRecord.idempotency_key
                == key,
            )
            .with_for_update()
        )

        if record:
            if record.request_hash != request_hash:
                raise DomainError(
                    "IDEMPOTENCY_KEY_REUSED",
                    "The idempotency key was already used with a different request.",
                    409,
                )

            if record.status == "COMPLETED":
                return IdempotencyAcquireResult(
                    replay=True,
                    record=record,
                )

            if record.status == "IN_PROGRESS":
                raise DomainError(
                    "REQUEST_ALREADY_IN_PROGRESS",
                    "The same request is already processing.",
                    409,
                )

        now = datetime.now(UTC)

        record = IdempotencyRecord(
            actor_key=actor_key,
            operation=operation,
            idempotency_key=key,
            request_hash=request_hash,
            status="IN_PROGRESS",
            expires_at=now
            + timedelta(hours=ttl_hours),
            created_at=now,
            updated_at=now,
        )

        self.session.add(record)

        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()

            raise DomainError(
                "REQUEST_ALREADY_IN_PROGRESS",
                "The same request is already processing.",
                409,
            )

        return IdempotencyAcquireResult(
            replay=False,
            record=record,
        )

    def complete(
        self,
        record: IdempotencyRecord,
        *,
        resource_type: str,
        resource_id,
        response_code: int,
        response_json: dict,
    ) -> None:
        record.status = "COMPLETED"

        record.resource_type = resource_type
        record.resource_id = resource_id

        record.response_code = response_code
        record.response_json = response_json

        record.updated_at = datetime.now(UTC)
```

One caution: **do not rollback the whole domain transaction inside** **`acquire()`** **after other changes are staged**. Acquire idempotency before business mutation, or use savepoints. The implementing engineer should account for this.

---

# 11. Audit service

`apps/api/app/domains/common/audit.py`

```python
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.models import AuditEvent


class AuditService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    def add(
        self,
        *,
        actor_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        correlation_id: str,
        tenant_id: UUID | None = None,
        legal_entity_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor_id,

            action=action,

            resource_type=resource_type,
            resource_id=resource_id,

            correlation_id=correlation_id,

            tenant_id=tenant_id,
            legal_entity_id=legal_entity_id,

            metadata_json=metadata or {},

            created_at=datetime.now(UTC),
        )

        self.session.add(event)

        return event
```

---

# 12. Capability registry

Extend the **existing** capability implementation instead of replacing it.

`apps/api/app/domains/capabilities/registry.py`

```python
from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class CapabilityState:
    name: str

    configured: bool
    effective: bool

    reason: str | None = None


class CapabilityRegistry:
    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    def state(
        self,
        name: str,
    ) -> CapabilityState:
        configured = bool(
            getattr(
                self.settings,
                f"{name}_enabled",
                False,
            )
        )

        if name == "provider_opportunities":
            dependencies = (
                self.settings.marketplace_matching_enabled
                and self.settings.provider_self_service_enabled
            )

        elif name == "quotes":
            dependencies = (
                self.settings.provider_self_service_enabled
            )

        elif name == "payments":
            dependencies = (
                self.settings.payments_enabled
                and self.settings.stripe_enabled
                and self.settings.online_checkout_enabled
            )

        elif name == "payouts":
            dependencies = (
                self.settings.payments_enabled
            )

        else:
            dependencies = True

        effective = (
            configured
            and dependencies
        )

        return CapabilityState(
            name=name,
            configured=configured,
            effective=effective,
            reason=None
            if effective
            else "disabled_or_dependency_unavailable",
        )

    def enabled(
        self,
        name: str,
    ) -> bool:
        return self.state(name).effective
```

The exact settings names need to use those already present in BREERO.

---

# 13. Capability dependency

```python
from fastapi import Depends

from app.core.errors import DomainError
from app.domains.capabilities.service import get_capability_registry


def require_capability(
    capability: str,
):
    async def dependency(
        registry=Depends(
            get_capability_registry
        ),
    ):
        if not registry.enabled(
            capability
        ):
            raise DomainError(
                "CAPABILITY_DISABLED",
                f"{capability} is not currently available.",
                404,
            )

    return dependency
```

---

# 14. Integration adapter contract

`apps/api/app/integrations/base.py`

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResult:
    provider: str

    success: bool

    external_id: str | None = None

    retryable: bool = False

    error_code: str | None = None

    retry_after_seconds: int | None = None


class IntegrationProvider(
    Protocol
):
    async def health(
        self,
    ) -> bool:
        ...

    async def publish(
        self,
        *,
        event_type: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProviderResult:
        ...
```

---

# 15. Specific adapter protocols

```python
from typing import Protocol


class EmailProvider(Protocol):
    async def send_transactional(
        self,
        *,
        recipient: str,
        template: str,
        data: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        ...


class SmsProvider(Protocol):
    async def send_transactional(
        self,
        *,
        recipient: str,
        template: str,
        data: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        ...


class Geocoder(Protocol):
    async def geocode(
        self,
        *,
        address: dict,
    ):
        ...


class ObjectStorage(Protocol):
    async def create_upload(
        self,
        *,
        key: str,
        content_type: str,
        max_bytes: int,
    ):
        ...

    async def create_download(
        self,
        *,
        key: str,
        expires_seconds: int,
    ):
        ...


class MalwareScanner(Protocol):
    async def scan(
        self,
        *,
        storage_key: str,
    ):
        ...


class PaymentProvider(Protocol):
    async def create_intent(
        self,
        **kwargs,
    ):
        ...

    async def refund(
        self,
        **kwargs,
    ):
        ...
```

---

# 16. Generic provider HTTP client

```python
import random
import asyncio

import httpx


class ProviderHttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        headers: dict[str, str],
        connect_timeout: float = 3,
        request_timeout: float = 10,
    ):
        self.base_url = (
            base_url.rstrip("/")
        )

        self.headers = headers

        self.timeout = httpx.Timeout(
            connect=connect_timeout,
            read=request_timeout,
            write=request_timeout,
            pool=connect_timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
        retries: int = 2,
    ) -> httpx.Response:
        headers = dict(
            self.headers
        )

        if idempotency_key:
            headers[
                "Idempotency-Key"
            ] = idempotency_key

        if correlation_id:
            headers[
                "X-Correlation-ID"
            ] = correlation_id

        last_error = None

        async with httpx.AsyncClient(
            timeout=self.timeout,
        ) as client:
            for attempt in range(
                retries + 1
            ):
                try:
                    response = (
                        await client.request(
                            method,
                            f"{self.base_url}{path}",
                            json=json,
                            headers=headers,
                        )
                    )

                    if response.status_code in {
                        429,
                        502,
                        503,
                        504,
                    }:
                        if attempt < retries:
                            delay = (
                                0.25
                                * (2**attempt)
                                + random.uniform(
                                    0,
                                    0.2,
                                )
                            )

                            await asyncio.sleep(
                                delay
                            )

                            continue

                    return response

                except (
                    httpx.TimeoutException,
                    httpx.NetworkError,
                ) as exc:
                    last_error = exc

                    if attempt >= retries:
                        raise

                    await asyncio.sleep(
                        0.25
                        * (2**attempt)
                    )

        raise RuntimeError(
            "provider request failed"
        ) from last_error
```

Do not retry all POSTs unless idempotency is guaranteed.

---

# 17. Codestra adapter

```python
from app.integrations.base import (
    ProviderResult,
)
from app.integrations.http import (
    ProviderHttpClient,
)


class CodestraAdapter:
    def __init__(
        self,
        client: ProviderHttpClient,
    ):
        self.client = client

    async def health(
        self,
    ) -> bool:
        try:
            response = (
                await self.client.request(
                    "GET",
                    "/health",
                    retries=0,
                )
            )

            return (
                response.status_code
                < 500
            )

        except Exception:
            return False

    async def publish(
        self,
        *,
        event_type: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> ProviderResult:
        response = (
            await self.client.request(
                "POST",
                "/events",
                json={
                    "event_type":
                        event_type,

                    "schema_version": 1,

                    "payload":
                        payload,
                },
                idempotency_key=(
                    idempotency_key
                ),
                correlation_id=(
                    correlation_id
                ),
            )
        )

        if (
            200
            <= response.status_code
            < 300
        ):
            body = (
                response.json()
                if response.content
                else {}
            )

            return ProviderResult(
                provider="CODESTRA",
                success=True,
                external_id=body.get(
                    "id"
                ),
            )

        retryable = (
            response.status_code
            in {
                429,
                502,
                503,
                504,
            }
        )

        return ProviderResult(
            provider="CODESTRA",

            success=False,

            retryable=retryable,

            error_code=(
                f"HTTP_{response.status_code}"
            ),
        )
```

Actual path/auth must match the existing Codestra contract.

---

# 18. Webhook verifier

`apps/api/app/integrations/webhook.py`

```python
import hashlib
import hmac
import time


class WebhookError(
    ValueError
):
    pass


def verify_hmac_sha256(
    *,
    secret: bytes,
    timestamp: str,
    signature: str,
    raw_body: bytes,
    tolerance_seconds: int = 300,
) -> None:
    try:
        parsed_timestamp = int(
            timestamp
        )
    except ValueError as exc:
        raise WebhookError(
            "invalid timestamp"
        ) from exc

    now = int(time.time())

    if abs(
        now - parsed_timestamp
    ) > tolerance_seconds:
        raise WebhookError(
            "timestamp outside tolerance"
        )

    signed_payload = (
        timestamp.encode("utf-8")
        + b"."
        + raw_body
    )

    expected = hmac.new(
        secret,
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected,
        signature,
    ):
        raise WebhookError(
            "invalid signature"
        )
```

---

# 19. Integration inbox model

Add via Alembic.

```python
class IntegrationInbox(
    Base
):
    __tablename__ = (
        "integration_inbox"
    )

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    provider = mapped_column(
        String(50),
        nullable=False,
    )

    external_event_id = (
        mapped_column(
            String(255),
            nullable=False,
        )
    )

    event_type = mapped_column(
        String(160),
        nullable=False,
    )

    schema_version = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )

    request_hash = mapped_column(
        String(64),
        nullable=False,
    )

    signature_verified = (
        mapped_column(
            Boolean,
            nullable=False,
        )
    )

    status = mapped_column(
        String(40),
        nullable=False,
        default="RECEIVED",
    )

    payload = mapped_column(
        JSONB,
        nullable=False,
    )

    received_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    processing_started_at = (
        mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
    )

    processed_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    attempt_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    next_attempt_at = (
        mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
    )

    last_error_code = (
        mapped_column(
            String(120),
            nullable=True,
        )
    )

    correlation_id = (
        mapped_column(
            String(120),
            nullable=False,
        )
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_event_id",
            name=(
                "uq_inbox_provider_event"
            ),
        ),
    )
```

---

# 20. Inbox service

```python
import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.integrations.models import IntegrationInbox


class InboxService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def accept(
        self,
        *,
        provider: str,
        external_event_id: str,
        event_type: str,
        raw_body: bytes,
        payload: dict,
        correlation_id: str,
        signature_verified: bool,
    ):
        existing = await self.session.scalar(
            select(
                IntegrationInbox
            ).where(
                IntegrationInbox.provider
                == provider,
                IntegrationInbox.external_event_id
                == external_event_id,
            )
        )

        if existing:
            return (
                existing,
                True,
            )

        item = IntegrationInbox(
            provider=provider,

            external_event_id=(
                external_event_id
            ),

            event_type=event_type,

            request_hash=(
                hashlib.sha256(
                    raw_body
                ).hexdigest()
            ),

            signature_verified=(
                signature_verified
            ),

            status="RECEIVED",

            payload=payload,

            correlation_id=(
                correlation_id
            ),

            received_at=(
                datetime.now(UTC)
            ),
        )

        self.session.add(item)

        await self.session.commit()

        return (
            item,
            False,
        )
```

Production implementation should also safely handle race-condition duplicate inserts via the DB unique constraint.

---

# 21. Generic webhook route pattern

```python
import json
import uuid

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
)

from app.db.session import get_session
from app.domains.integrations.inbox import InboxService
from app.integrations.webhook import (
    WebhookError,
    verify_hmac_sha256,
)


router = APIRouter()


@router.post(
    "/codestra",
    status_code=202,
)
async def codestra_webhook(
    request: Request,

    event_id: str = Header(
        alias="X-Event-ID"
    ),

    timestamp: str = Header(
        alias="X-Timestamp"
    ),

    signature: str = Header(
        alias="X-Signature"
    ),

    session=Depends(
        get_session
    ),
):
    raw_body = (
        await request.body()
    )

    try:
        verify_hmac_sha256(
            secret=(
                request.app.state
                .codestra_webhook_secret
            ),

            timestamp=timestamp,

            signature=signature,

            raw_body=raw_body,
        )

    except WebhookError:
        raise HTTPException(
            status_code=401,
            detail={
                "code":
                    "INVALID_WEBHOOK",
            },
        )

    try:
        payload = json.loads(
            raw_body
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail={
                "code":
                    "INVALID_JSON",
            },
        )

    correlation_id = (
        request.headers.get(
            "X-Correlation-ID"
        )
        or str(uuid.uuid4())
    )

    item, duplicate = (
        await InboxService(
            session
        ).accept(
            provider="CODESTRA",

            external_event_id=(
                event_id
            ),

            event_type=payload[
                "event_type"
            ],

            raw_body=raw_body,

            payload=payload,

            correlation_id=(
                correlation_id
            ),

            signature_verified=True,
        )
    )

    return {
        "accepted": True,
        "duplicate": duplicate,
        "id": str(item.id),
    }
```

Use provider-specific verification for Stripe/Klyrow/Telnexa/etc.

---

# 22. Outbox worker

The current BREERO outbox should be extended rather than replaced.

Core claim logic:

```python
async def claim_batch(
    session,
    *,
    worker_id: str,
    batch_size: int,
    lease_seconds: int,
):
    now = datetime.now(UTC)

    events = list(
        (
            await session.scalars(
                select(
                    IntegrationEvent
                )
                .where(
                    IntegrationEvent.status.in_(
                        [
                            "PENDING",
                            "FAILED_RETRYABLE",
                            "RETRYING",
                        ]
                    ),
                    IntegrationEvent.next_attempt_at
                    <= now,
                    or_(
                        IntegrationEvent.lease_expires_at
                        .is_(None),

                        IntegrationEvent.lease_expires_at
                        < now,
                    ),
                )
                .order_by(
                    IntegrationEvent.created_at
                )
                .with_for_update(
                    skip_locked=True
                )
                .limit(
                    batch_size
                )
            )
        ).all()
    )

    for event in events:
        event.status = (
            "PROCESSING"
        )

        event.claim_token = (
            worker_id
        )

        event.claimed_at = now

        event.lease_expires_at = (
            now
            + timedelta(
                seconds=lease_seconds
            )
        )

    await session.commit()

    return events
```

Use the repo's actual existing field names.

---

# 23. Storage object model

```python
class StorageObject(Base):
    __tablename__ = (
        "storage_objects"
    )

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_user_id = (
        mapped_column(
            UUID(as_uuid=True),
            nullable=True,
        )
    )

    provider_id = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    purpose = mapped_column(
        String(60),
        nullable=False,
    )

    storage_key = mapped_column(
        String(512),
        nullable=False,
        unique=True,
    )

    original_filename = (
        mapped_column(
            String(255),
            nullable=False,
        )
    )

    content_type = mapped_column(
        String(120),
        nullable=False,
    )

    size_bytes = mapped_column(
        BigInteger,
        nullable=True,
    )

    sha256 = mapped_column(
        String(64),
        nullable=True,
    )

    status = mapped_column(
        String(40),
        nullable=False,
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
```

States:

```text
PENDING_UPLOAD
UPLOADED
SCANNING
CLEAN
QUARANTINED
REJECTED
DELETED
```

---

# 24. Upload service

```python
import uuid
from datetime import UTC, datetime

from app.core.errors import DomainError


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}


MAX_UPLOAD_BYTES = (
    20 * 1024 * 1024
)


class UploadService:
    def __init__(
        self,
        session,
        storage,
    ):
        self.session = session
        self.storage = storage

    async def create_upload(
        self,
        *,
        principal,
        purpose: str,
        filename: str,
        content_type: str,
    ):
        if (
            content_type
            not in ALLOWED_CONTENT_TYPES
        ):
            raise DomainError(
                "UNSUPPORTED_FILE_TYPE",
                "This file type is not supported.",
                422,
            )

        object_id = uuid.uuid4()

        key = (
            f"{purpose.lower()}/"
            f"{object_id}"
        )

        item = StorageObject(
            id=object_id,

            owner_user_id=(
                principal.user_id
            ),

            purpose=purpose,

            storage_key=key,

            original_filename=(
                filename
            ),

            content_type=(
                content_type
            ),

            status=(
                "PENDING_UPLOAD"
            ),

            created_at=(
                datetime.now(UTC)
            ),
        )

        self.session.add(item)

        upload_target = (
            await self.storage
            .create_upload(
                key=key,

                content_type=(
                    content_type
                ),

                max_bytes=(
                    MAX_UPLOAD_BYTES
                ),
            )
        )

        await self.session.commit()

        return {
            "id": str(item.id),
            "upload": upload_target,
        }
```

---

# 25. Upload API

```http
POST /api/v2/uploads
POST /api/v2/uploads/{id}/complete

GET /api/v2/uploads/{id}

DELETE /api/v2/uploads/{id}
```

Never expose the underlying bucket as a permanent public URL.

---

# 26. Operational exception model

```python
class OperationalException(
    Base
):
    __tablename__ = (
        "operational_exceptions"
    )

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    exception_type = (
        mapped_column(
            String(100),
            nullable=False,
        )
    )

    severity = mapped_column(
        String(20),
        nullable=False,
    )

    status = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
    )

    resource_type = (
        mapped_column(
            String(100),
            nullable=False,
        )
    )

    resource_id = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    assigned_to = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    details_json = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    resolved_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
```

---

# 27. Scheduler tasks

`apps/api/app/workers/scheduler.py`

Create scheduled jobs for:

```python
SCHEDULED_TASKS = {
    "expire_booking_holds":
        "*/1 * * * *",

    "expire_opportunities":
        "*/5 * * * *",

    "expire_quotes":
        "*/5 * * * *",

    "credential_expiry":
        "0 * * * *",

    "stale_project_requests":
        "*/15 * * * *",

    "unassigned_jobs":
        "*/5 * * * *",

    "late_jobs":
        "*/5 * * * *",

    "review_reminders":
        "0 */6 * * *",

    "retention":
        "0 3 * * *",
}
```

Use existing Celery beat/scheduler patterns rather than introducing another scheduler technology.

---

# 28. Observability middleware

```python
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware


class ObservabilityMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request,
        call_next,
    ):
        request_id = (
            request.headers.get(
                "X-Request-ID"
            )
            or str(uuid.uuid4())
        )

        correlation_id = (
            request.headers.get(
                "X-Correlation-ID"
            )
            or request_id
        )

        started = (
            time.perf_counter()
        )

        request.state.request_id = (
            request_id
        )

        request.state.correlation_id = (
            correlation_id
        )

        response = await call_next(
            request
        )

        duration = (
            time.perf_counter()
            - started
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        response.headers[
            "X-Correlation-ID"
        ] = correlation_id

        # emit metric/log here

        return response
```

---

# 29. Health endpoints

```python
from fastapi import APIRouter
from sqlalchemy import text


router = APIRouter()


@router.get(
    "/health/live"
)
async def live():
    return {
        "status": "live"
    }


@router.get(
    "/health/ready"
)
async def ready(
    session=Depends(
        get_session
    ),
):
    await session.execute(
        text("SELECT 1")
    )

    return {
        "status": "ready",
        "database": "ok",
    }


@router.get(
    "/health/version"
)
async def version():
    return {
        "version":
            settings.app_version,

        "git_sha":
            settings.git_sha,

        "migration_head":
            settings.migration_head,
    }
```

Do not hardwire disabled external vendors into readiness.

---

# 30. Backup script

Add a production-reviewed script such as:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${BACKUP_DIR:?}"
: "${POSTGRES_HOST:?}"
: "${POSTGRES_DB:?}"
: "${POSTGRES_USER:?}"
: "${PGPASSFILE:?}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"

target="${BACKUP_DIR}/breero-${timestamp}.dump"

pg_dump \
  --host="${POSTGRES_HOST}" \
  --username="${POSTGRES_USER}" \
  --dbname="${POSTGRES_DB}" \
  --format=custom \
  --no-password \
  --file="${target}"

sha256sum \
  "${target}" \
  > "${target}.sha256"

echo "BACKUP_FILE=${target}"
```

The real production deployment should encrypt and copy it off-host.

Do not print the password.

---

# 31. Restore verification script

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${BACKUP_FILE:?}"
: "${RESTORE_DATABASE_URL:?}"

sha256sum -c \
  "${BACKUP_FILE}.sha256"

pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --dbname="${RESTORE_DATABASE_URL}" \
  "${BACKUP_FILE}"

alembic current

pytest -q \
  tests/smoke/test_restored_database.py
```

Only run against an isolated restore DB.

Never production.

---

# 32. GitHub backend CI

Add/extend workflow roughly:

```yaml
name: Backend V2

on:
  pull_request:
    paths:
      - "apps/api/**"
      - "packages/types/**"
      - ".github/workflows/backend-v2.yml"

jobs:
  quality:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgis/postgis:17-3.5

        env:
          POSTGRES_DB: breero_test
          POSTGRES_USER: breero
          POSTGRES_PASSWORD: test-only-password

        ports:
          - 5432:5432

        options: >-
          --health-cmd
          "pg_isready -U breero -d breero_test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 20

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: |
          python -m pip install --upgrade pip
          pip install -e 'apps/api[dev]'

      - run: |
          cd apps/api
          ruff check app tests
          python -m compileall -q app tests

      - run: |
          cd apps/api
          alembic upgrade head

      - run: |
          cd apps/api
          pytest -q

      - run: |
          cd apps/api
          python scripts/generate_openapi.py

      - run: |
          pnpm install --frozen-lockfile
          pnpm contract:check
```

Pin actions to reviewed versions/digests according to your supply-chain policy.

---

# 33. Security CI

Add:

```text
dependency audit

container scan

secret scan

SBOM generation

migration drift

OpenAPI drift
```

Do not automatically weaken failing tests.

---

# 34. Backend P0 tests

At minimum add:

```text
test_oidc_wrong_issuer_denied

test_oidc_wrong_audience_denied

test_external_identity_is_issuer_subject

test_customer_cannot_read_other_customer_request

test_provider_cannot_read_other_provider_opportunity

test_worker_cannot_execute_unassigned_job

test_disabled_capability_rejects_command

test_idempotency_same_key_same_body_replays

test_idempotency_same_key_different_body_conflicts

test_concurrent_opportunity_accept_creates_one_lead

test_outbox_worker_reclaims_stale_lease

test_disabled_integration_parks_event

test_inbox_duplicate_event_has_one_business_effect

test_webhook_invalid_signature_denied

test_webhook_timestamp_replay_denied

test_upload_wrong_content_type_rejected

test_upload_not_available_before_clean_scan

test_backup_restore_migration_smoke
```

---

# 35. Feature branch order after P0

Once P0 is green:

```text
be/marketplace-v2-catalog
be/marketplace-v2-project-requests

be/marketplace-v2-provider-core
be/marketplace-v2-provider-trust
be/marketplace-v2-provider-availability

be/marketplace-v2-matching
be/marketplace-v2-opportunities

be/marketplace-v2-quotes
be/marketplace-v2-messaging

be/marketplace-v2-booking-job
be/marketplace-v2-reviews

be/marketplace-v2-notifications
be/marketplace-v2-disputes

be/marketplace-v2-ops
be/marketplace-v2-admin

be/marketplace-v2-third-party-adapters
be/marketplace-v2-analytics
```

Then frontend implementation follows each stable backend contract.

---

## What remains vendor/environment-specific

The implementation agent can write all interfaces and tests now, but the following cannot be certified without the real environment:

```text
Keycloak production client configuration

Codestra production service credentials

Codestra mTLS certificates

Klyrow production service authorization

Telnexa production authorization

Odoo production/staging credentials

n8n approved workflow IDs

real object-storage credentials

real malware scanning provider

real geocoder API

Stripe production account

DNS/TLS/firewall

backup destination

monitoring/alert destinations
```

These should be wired through mounted secrets and configuration, never committed.

The most important thing to give the write-enabled developer is therefore not another architecture memo—it is this **P0 implementation set** plus the feature branch order. Once these primitives are green, every marketplace feature can use the same authorization, idempotency, auditing, storage, outbox/inbox, exception, observability, backup, and deployment systems rather than reimplementing reliability separately.