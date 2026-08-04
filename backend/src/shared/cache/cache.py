"""
Cache abstraction + rate limiting."Shared Notification Infrastructure" (cache.py,
check_rate_limit); scalability follow-up requested during the reset-
password web page work.

DESIGN
------
RateLimitCache is the formal contract every caller in this codebase
depends on -- auth_service.py (login lockout), otp_service.py and
password_reset_service.py (send-rate limits, via EmailService),
reset_password_routes.py (the web fallback page), and any future
rate-limited endpoint. None of them may depend on which concrete class
implements it.

Two access patterns are covered, because callers genuinely need both:
  - check_rate_limit() -- the common case: "is this action still within
    its limit" (OTP/email/reset-page limits: increment-and-check in one
    call).
  - get_count() / increment() / reset() -- lower-level primitives, for
    callers needing finer control than a single increment (login
    lockout: check the count WITHOUT incrementing on a successful
    login, increment only on failure, reset on success).

InMemoryCache is today's implementation -- correct for a single Flask
process, which is the current deployment. It does NOT share state
across multiple worker processes (each gets its own dict), so a rate
limit enforced this way becomes "limit x worker count" the moment this
runs behind more than one process.

THE SWAP POINT is the `cache` singleton assignment near the bottom of
this file. When this needs to run as more than one worker process, a
Redis-backed implementation satisfying RateLimitCache replaces
InMemoryCache on that ONE line. No caller listed above changes --
that is the entire point of depending on RateLimitCache rather than on
InMemoryCache directly.
"""
from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional


class RateLimitCache(ABC):
    """Formal contract for anything backing rate-limit counters. A
    future Redis-backed implementation must satisfy this exact
    interface."""

    @abstractmethod
    def get(self, key: str):
        ...

    @abstractmethod
    def get_count(self, key: str) -> int:
        """Read-only: current integer counter value, 0 if absent/expired.
        Does NOT increment."""
        ...

    @abstractmethod
    def set(self, key: str, value, ttl_seconds: Optional[float] = None) -> None:
        ...

    @abstractmethod
    def increment(self, key: str, ttl_seconds: Optional[float] = None) -> int:
        """Atomically increments an integer counter, creating it at 1 if
        absent."""
        ...

    @abstractmethod
    def reset(self, key: str) -> None:
        """Clears a single key."""
        ...


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value, expires_at: Optional[float]):
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() >= self.expires_at


class InMemoryCache(RateLimitCache):
    """Process-local implementation. Thread-safe within one process via
    a lock; NOT safe across multiple processes -- see this module's
    docstring."""

    def __init__(self):
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                self._store.pop(key, None)
                return None
            return entry.value

    def get_count(self, key: str) -> int:
        value = self.get(key)
        return value if isinstance(value, int) else 0

    def set(self, key: str, value, ttl_seconds: Optional[float] = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        with self._lock:
            self._store[key] = _CacheEntry(value, expires_at)

    def increment(self, key: str, ttl_seconds: Optional[float] = None) -> int:
        with self._lock:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
                self._store[key] = _CacheEntry(1, expires_at)
                return 1
            entry.value += 1
            return entry.value

    def reset(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Test-only helper, NOT part of the RateLimitCache contract --
        production code should never call this."""
        with self._lock:
            self._store.clear()


# ------------------------------------------------------------------------
# THE SWAP POINT
# ------------------------------------------------------------------------
# Every caller in this codebase imports THIS singleton by name -- never
# InMemoryCache directly. A future Redis-backed implementation replaces
# only the right-hand side below:
#
#     cache: RateLimitCache = RedisCache(redis_url=...)
#
# No other file changes.
cache: RateLimitCache = InMemoryCache()


def check_rate_limit(key: str, max_count: int, window_seconds: int) -> bool:
    """Returns True if the action identified by `key` is still within its
    rate limit (and records this attempt), False if the limit has already
    been exceeded."""
    count = cache.increment(key, ttl_seconds=window_seconds)
    return count <= max_count