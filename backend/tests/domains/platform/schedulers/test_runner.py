"""
runner.make_safe() and the listener/observer mechanism — no engine, no DB,
no Flask needed. Proves: success path notifies listeners correctly,
exceptions are caught and never propagate to the caller, a job returning
the wrong type is treated as a failure (not a crash), and one broken
listener never prevents another listener from being notified.
"""

from __future__ import annotations

import pytest

from src.domains.platform.schedulers import runner
from src.shared.scheduling_types import JobExecutionOutcome, JobResult


@pytest.fixture(autouse=True)
def _clear_listeners():
    # runner._listeners is module-level global state; isolate tests from
    # each other and from any real listeners (e.g. security.monitor) that
    # may have registered elsewhere in the test session.
    original = runner._listeners[:]
    runner._listeners.clear()
    yield
    runner._listeners[:] = original


def test_successful_job_notifies_listener_with_success_outcome():
    received = []
    runner.add_listener(received.append)

    safe = runner.make_safe("job_a", lambda: JobResult(success=True, count=3, detail="ok"))
    safe()

    assert len(received) == 1
    outcome = received[0]
    assert isinstance(outcome, JobExecutionOutcome)
    assert outcome.job_name == "job_a"
    assert outcome.success is True
    assert outcome.result.count == 3


def test_raising_job_is_caught_and_notifies_failure_outcome():
    received = []
    runner.add_listener(received.append)

    def bad_job():
        raise RuntimeError("boom")

    safe = runner.make_safe("job_b", bad_job)
    safe()  # must not raise

    assert len(received) == 1
    assert received[0].success is False
    assert received[0].error == "boom"


def test_non_jobresult_return_is_treated_as_failure_not_a_crash():
    received = []
    runner.add_listener(received.append)

    safe = runner.make_safe("job_c", lambda: "not a JobResult")
    safe()  # must not raise

    assert received[0].success is False


def test_one_broken_listener_does_not_block_another():
    good_received = []

    def broken_listener(outcome):
        raise RuntimeError("listener is broken")

    runner.add_listener(broken_listener)
    runner.add_listener(good_received.append)

    safe = runner.make_safe("job_d", lambda: JobResult(success=True))
    safe()  # must not raise despite broken_listener

    assert len(good_received) == 1


def test_context_factory_is_invoked_around_execution():
    entered = []

    class _Ctx:
        def __enter__(self):
            entered.append("enter")
        def __exit__(self, *a):
            entered.append("exit")

    safe = runner.make_safe("job_e", lambda: JobResult(success=True), context_factory=_Ctx)
    safe()

    assert entered == ["enter", "exit"]
