"""
The contract every detector must satisfy.

Fixed in Phase 1 so Phase 2 detectors are additive. A detector reads audit
data and returns findings; it never mutates accounts and never blocks a
request. Enforcement (lock, disable, alert) is a separate decision made by
whatever consumes the findings — keeping detection side-effect-free is
what makes it safe to iterate on rules without risking production data.
"""

from __future__ import annotations

import abc
import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


class FindingType(str, enum.Enum):
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    SUSPICIOUS_DEVICE = "suspicious_device"
    ANOMALOUS_VOLUME = "anomalous_volume"


@dataclass
class Finding:
    """One thing a detector noticed. Advisory only — never an action."""
    finding_type: FindingType
    severity: str
    summary: str
    subject: Optional[str] = None       # the email / IP / device implicated
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: dict[str, Any] = field(default_factory=dict)


class Detector(abc.ABC):
    """
    Base class for all detectors.

    Deliberately narrow: given a time window, look at audit data, return
    findings. No database writes, no account changes, no notifications.
    """

    name: str = "unnamed_detector"

    @abc.abstractmethod
    def run(self, since: datetime) -> list[Finding]:
        raise NotImplementedError
