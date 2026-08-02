"""
Detection engine — runs registered detectors and collects findings.

Phase 1: functional but with nothing registered to run, so it is a no-op
until Phase 2 adds detectors. Present now so the execution shape (each
detector isolated, one failure never stopping the others) is settled
rather than improvised later — the same isolation discipline the
scheduler's runner already applies to jobs.
"""

from __future__ import annotations

import logging
from datetime import datetime

from src.domains.security.detection.interfaces import Finding
from src.domains.security.detection.registry import all_detectors

logger = logging.getLogger(__name__)


def run_all(since: datetime) -> list[Finding]:
    """
    Run every registered detector over the window starting at `since`.
    A detector that raises is logged and skipped — one broken rule must
    not prevent every other rule from reporting.
    """
    findings: list[Finding] = []
    for detector in all_detectors():
        try:
            findings.extend(detector.run(since))
        except Exception:  # noqa: BLE001 — isolate detector failures
            logger.exception("detector '%s' raised", detector.name)
    return findings
