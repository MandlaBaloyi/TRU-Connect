"""
Safe execution wrapper + the observer hook Security listens through --
unchanged logic, import path moved to master_scheduler (previously
domains/platform/schedulers/runner.py).
"""

from __future__ import annotations

from src.master_scheduler import runner
from src.shared.scheduling.scheduling_types import JobExecutionOutcome, JobResult


def test_make_safe_wraps_a_successful_job():
    calls = []
    safe = runner.make_safe("test_job", lambda: JobResult(success=True, count=3))
    safe()  # must not raise
    assert calls == []  # no exception escaped


def test_make_safe_swallows_exceptions():
    """A job that raises must never crash the scheduler -- the whole
    point of wrapping every job in make_safe()."""
    def _failing_job():
        raise ValueError("boom")

    safe = runner.make_safe("failing_job", _failing_job)
    safe()  # must not raise, despite the job itself raising


def test_make_safe_rejects_non_job_result_return_value():
    """A job returning the wrong type is caught and logged, not left to
    crash the scheduler with an unrelated error deeper in the stack."""
    safe = runner.make_safe("bad_job", lambda: "not a JobResult")
    safe()  # must not raise -- make_safe catches the TypeError internally


def test_context_factory_is_applied_around_the_job():
    """Confirms the Flask-app-context wrapping trigger.py relies on
    actually happens -- a job run through make_safe with a
    context_factory must execute INSIDE that context."""
    entered = []

    class _FakeContext:
        def __enter__(self):
            entered.append("enter")
        def __exit__(self, *exc):
            entered.append("exit")

    safe = runner.make_safe(
        "ctx_job",
        lambda: JobResult(success=True),
        context_factory=lambda: _FakeContext(),
    )
    safe()
    assert entered == ["enter", "exit"]


def test_listeners_are_notified_after_execution():
    received = []
    runner.add_listener(lambda outcome: received.append(outcome.job_name))

    safe = runner.make_safe("notify_job", lambda: JobResult(success=True))
    safe()

    assert "notify_job" in received


def test_listeners_are_notified_even_when_the_job_fails():
    """Security's monitor.py needs to know about failures too, not just
    successes -- that's the whole point of health tracking."""
    received = []
    runner.add_listener(lambda outcome: received.append(outcome.job_name))

    def _failing_job():
        raise RuntimeError("expected failure")

    safe = runner.make_safe("failing_notify_job", _failing_job)
    safe()

    assert "failing_notify_job" in received


def test_a_broken_listener_does_not_break_execution():
    """One listener raising must never stop the job from having run, or
    stop other listeners from being notified."""
    def _broken_listener(outcome):
        raise RuntimeError("listener is broken")

    runner.add_listener(_broken_listener)

    safe = runner.make_safe("resilient_job", lambda: JobResult(success=True))
    safe()  # must not raise, despite the broken listener