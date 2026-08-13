import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.operations import dispatcher_queue
from app.domains.public_submissions.models import DownstreamStatus, SubmissionType


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


@pytest.mark.asyncio
async def test_dispatcher_queue_exposes_pending_manual_work_and_audit_history() -> None:
    request_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    created_at = datetime.now(UTC) - timedelta(minutes=10)
    submission = SimpleNamespace(
        id=request_id,
        submission_type=SubmissionType.SERVICE_REQUEST,
        created_at=created_at,
        downstream_status=DownstreamStatus.PENDING_CONFIGURATION,
        payload={
            "name": "Owner Controlled Canary",
            "customer_timezone": "America/New_York",
            "geoapify_verification_state": "PENDING_MANUAL_VALIDATION",
            "manual_dispatch_state": "PENDING_MANUAL_DISPATCH",
            "provider_assigned": False,
            "contact_attempts": [],
        },
    )
    audit = SimpleNamespace(
        resource_id=request_id,
        action="request.reviewed",
        actor_id=actor_id,
        metadata_json={"outcome": "follow_up_required"},
        created_at=created_at + timedelta(minutes=1),
    )
    session = SimpleNamespace(scalars=AsyncMock(side_effect=[ScalarResult([submission]), ScalarResult([audit])]))

    result = await dispatcher_queue(session=session, _=SimpleNamespace())

    assert len(result) == 1
    item = result[0]
    assert item.request_id == request_id
    assert item.required_follow_up is True
    assert item.address_verification_state == "PENDING_MANUAL_VALIDATION"
    assert item.manual_dispatch_state == "PENDING_MANUAL_DISPATCH"
    assert item.provider_assigned is False
    assert item.customer_timezone == "America/New_York"
    assert item.request_age_seconds >= 600
    assert item.audit_history[0].actor_id == actor_id
