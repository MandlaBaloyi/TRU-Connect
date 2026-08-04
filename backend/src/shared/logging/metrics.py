"""
In-memory metrics counters.
 "Shared Notification Infrastructure, "MONITORING" and
"METRICS" -- "Track: Emails sent, Emails failed, Retry count, Average
send time, SMTP latency, Queue depth, Success rate, Failure rate" and
"Collect metrics for: OTP emails, Password reset emails, Welcome emails,
Invitation emails, Delivery failures, SMTP reconnects."

DESIGN
------
Plain in-memory counters/timers, process-local. This is a placeholder
for a real metrics backend (Prometheus, StatsD, CloudWatch, Datadog,
etc.) -- the interface (record_sent / record_failed / record_send_time)
is what every caller uses, so swapping the backend later means changing
only this file.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict


class _MetricsRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._sent_counts: dict[str, int] = defaultdict(int)
        self._failed_counts: dict[str, int] = defaultdict(int)
        self._retry_counts: dict[str, int] = defaultdict(int)
        self._send_durations_seconds: list[float] = []

    def record_sent(self, template_name: str) -> None:
        with self._lock:
            self._sent_counts[template_name] += 1

    def record_failed(self, template_name: str) -> None:
        with self._lock:
            self._failed_counts[template_name] += 1

    def record_retry(self, template_name: str) -> None:
        with self._lock:
            self._retry_counts[template_name] += 1

    def record_send_duration(self, seconds: float) -> None:
        with self._lock:
            self._send_durations_seconds.append(seconds)

    def snapshot(self) -> dict:
        with self._lock:
            total_sent = sum(self._sent_counts.values())
            total_failed = sum(self._failed_counts.values())
            total_attempts = total_sent + total_failed
            avg_duration = (
                sum(self._send_durations_seconds) / len(self._send_durations_seconds)
                if self._send_durations_seconds
                else 0.0
            )
            return {
                "sent_by_template": dict(self._sent_counts),
                "failed_by_template": dict(self._failed_counts),
                "retries_by_template": dict(self._retry_counts),
                "total_sent": total_sent,
                "total_failed": total_failed,
                "success_rate": (total_sent / total_attempts) if total_attempts else 1.0,
                "failure_rate": (total_failed / total_attempts) if total_attempts else 0.0,
                "average_send_time_seconds": avg_duration,
            }


metrics = _MetricsRegistry()


class Timer:
    """Small context manager for timing a block of code and recording it
    into metrics -- used around the actual SMTP send call."""

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_seconds = time.monotonic() - self._start
