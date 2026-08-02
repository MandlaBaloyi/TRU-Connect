"""
Phase 1 detection is structure only — these tests pin the contract so
Phase 2 detectors are additive, and prove failure isolation now rather
than discovering it when the first real detector misbehaves.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domains.security.detection import engine, registry
from src.domains.security.detection.interfaces import Detector, Finding, FindingType


@pytest.fixture(autouse=True)
def _clean_registry():
    registry.clear()
    yield
    registry.clear()


def test_no_detectors_registered_in_phase_1():
    assert registry.all_detectors() == []


def test_engine_returns_nothing_when_no_detectors():
    assert engine.run_all(datetime.now(timezone.utc)) == []


def test_engine_collects_findings_from_registered_detector():
    class _Fake(Detector):
        name = "fake"
        def run(self, since):
            return [Finding(FindingType.BRUTE_FORCE, "high", "5 failures", subject="1.2.3.4")]

    registry.register(_Fake())
    findings = engine.run_all(datetime.now(timezone.utc))

    assert len(findings) == 1
    assert findings[0].finding_type is FindingType.BRUTE_FORCE


def test_one_broken_detector_does_not_stop_the_others():
    class _Broken(Detector):
        name = "broken"
        def run(self, since):
            raise RuntimeError("bad rule")

    class _Good(Detector):
        name = "good"
        def run(self, since):
            return [Finding(FindingType.ANOMALOUS_VOLUME, "low", "spike")]

    registry.register(_Broken())
    registry.register(_Good())

    findings = engine.run_all(datetime.now(timezone.utc))
    assert len(findings) == 1
