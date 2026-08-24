import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.api.v1.operations import dispatcher_queue, update_dispatcher_queue_item
from app.domains.public_submissions.models import DownstreamStatus, SubmissionType
from app.domains.public_submissions.schemas import DispatcherQueueUpdate


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


def test_dispatcher_update_schema_rejects_confirmation_assignment_and_payment_states() -> None:
    for forbidden in ("CONFIRMED", "PROVIDER_ASSIGNED", "PAID", "SCHEDULED"):
        with pytest.raises(ValidationError):
            DispatcherQueueUpdate(manual_dispatch_state=forbidden)


@pytest.mark.asyncio
async def test_dispatcher_update_records_contact_attempt_and_audit() -> None:
    request_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    submission = SimpleNamespace(id=request_id, payload={"contact_attempts": []})
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=submission),
        add=lambda value: setattr(session, "added", value),
        commit=AsyncMock(),
    )

    await update_dispatcher_queue_item(
        request_id=request_id,
        update=DispatcherQueueUpdate(
            manual_dispatch_state="CUSTOMER_CONTACTED",
            contact_outcome="CUSTOMER_REACHED",
            required_follow_up=True,
            note="Scope requires a provider quote",
        ),
        session=session,
        user=SimpleNamespace(id=actor_id),
    )

    assert submission.payload["manual_dispatch_state"] == "CUSTOMER_CONTACTED"
    assert submission.payload.get("provider_assigned") is not True
    assert submission.payload["contact_attempts"][0]["actor_id"] == str(actor_id)
    assert session.added.action == "manual_dispatch.update"
    assert "note" not in session.added.metadata_json
    session.commit.assert_awaited_once()
