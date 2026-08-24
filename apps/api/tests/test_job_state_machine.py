import pytest

from app.domains.jobs.models import JobStatus
from app.domains.jobs.service import TRANSITIONS


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (JobStatus.CREATED, JobStatus.MATCHING),
        (JobStatus.OFFERED, JobStatus.ASSIGNED),
        (JobStatus.ASSIGNED, JobStatus.EN_ROUTE),
        (JobStatus.EN_ROUTE, JobStatus.ON_SITE),
        (JobStatus.ON_SITE, JobStatus.DIAGNOSING),
        (JobStatus.DIAGNOSING, JobStatus.AWAITING_APPROVAL),
        (JobStatus.AWAITING_APPROVAL, JobStatus.IN_PROGRESS),
        (JobStatus.IN_PROGRESS, JobStatus.COMPLETED),
    ],
)
def test_operational_happy_path_transitions_are_allowed(source, target):
    assert target in TRANSITIONS[source]


@pytest.mark.parametrize("terminal", [JobStatus.COMPLETED, JobStatus.CANCELLED])
def test_terminal_states_cannot_transition(terminal):
    assert TRANSITIONS[terminal] == set()


def test_job_cannot_skip_assignment_and_execution():
    assert JobStatus.COMPLETED not in TRANSITIONS[JobStatus.CREATED]
    assert JobStatus.IN_PROGRESS not in TRANSITIONS[JobStatus.ASSIGNED]
