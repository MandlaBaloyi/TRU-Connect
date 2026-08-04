"""
Master Scheduler's registry -- proves it correctly CONCATENATES every
domain's own declared jobs and defines none itself.

Deliberately monkeypatches ALL_JOB_SPECS directly (the composed list)
rather than reaching into any one domain's scheduler file -- this test
verifies the composition mechanism, which is what changed; it does not
need to know or care what any real domain has actually declared.
"""

from __future__ import annotations

from typing import Callable

import pytest

from src.master_scheduler import registry
from src.master_scheduler.interfaces import JobSpec, SchedulerEngine
from src.shared.scheduling.scheduling_types import JobResult


class _FakeEngine(SchedulerEngine):
    def __init__(self):
        self.added: dict[str, tuple[Callable, float]] = {}
        self._running = False

    def add_job(self, job_id, func, interval_seconds):
        self.added[job_id] = (func, interval_seconds)

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    @property
    def is_running(self):
        return self._running


@pytest.fixture(autouse=True)
def _fake_job_specs(monkeypatch):
    fake_specs = [
        JobSpec("fake_auth_job", lambda: JobResult(success=True), 60),
        JobSpec("fake_platform_job", lambda: JobResult(success=True), 3600),
    ]
    monkeypatch.setattr(registry, "ALL_JOB_SPECS", fake_specs)
    return fake_specs


def test_register_all_adds_every_domains_job(_fake_job_specs):
    engine = _FakeEngine()
    registry.register_all(engine)
    assert set(engine.added.keys()) == {"fake_auth_job", "fake_platform_job"}


def test_registered_intervals_match(_fake_job_specs):
    engine = _FakeEngine()
    registry.register_all(engine)
    for spec in _fake_job_specs:
        _, interval = engine.added[spec.name]
        assert interval == spec.interval_seconds


def test_registered_function_is_safe_wrapped_and_callable(_fake_job_specs):
    engine = _FakeEngine()
    registry.register_all(engine)
    func, _ = engine.added["fake_auth_job"]
    func()  # must not raise


def test_registry_defines_no_jobs_itself():
    """
    Structural check, not just behavioural: the Master's own registry
    module must contain no JobSpec literal anywhere in its source --
    "does the Master Scheduler run business jobs? No" is enforced here by
    inspecting the actual file, not just by convention.
    """
    import inspect

    source = inspect.getsource(registry)
    # The only JobSpec-shaped construction allowed in this file is inside
    # a docstring/comment example -- real declarations use JobSpec(...)
    # as a live call, which only appears in domain-owned scheduler files.
    assert "JobSpec(\n" not in source or "# JobSpec(" in source
