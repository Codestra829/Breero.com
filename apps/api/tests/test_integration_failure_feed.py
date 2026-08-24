from app.api.v1.integrations import FAILURE_STATUSES
from app.domains.common.outbox import EventStatus


def test_failure_feed_includes_terminal_delivery_failures() -> None:
    assert EventStatus.FAILED_TERMINAL in FAILURE_STATUSES
    assert EventStatus.FAILED in FAILURE_STATUSES
    assert EventStatus.DEAD_LETTER in FAILURE_STATUSES
