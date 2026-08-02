"""
Detector registry — the list of active detectors.

Empty in Phase 1 by design. Phase 2 registers detectors here, and
whatever runs them (most likely a scheduled job registered through
platform/schedulers/registry.py, following the same "Platform owns when,
a domain owns what" split already established) iterates this list.
"""

from __future__ import annotations

from src.domains.security.detection.interfaces import Detector

_detectors: list[Detector] = []


def register(detector: Detector) -> None:
    _detectors.append(detector)


def all_detectors() -> list[Detector]:
    return list(_detectors)


def clear() -> None:
    """Test helper."""
    _detectors.clear()
