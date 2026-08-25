"""
Tests for services/abuse_tracking.py -- the real lockout mechanism
covering the "someone deliberately crafting a malicious ZIP" case,
distinct from every ordinary validation error a supplier can honestly
hit.
"""
from __future__ import annotations

import uuid

import pytest

from src.domains.supplier.bulk_import.services import abuse_tracking
from src.shared.cache.cache import cache


@pytest.fixture(autouse=True)
def _clean_cache():
    yield
    cache.clear()


def test_not_locked_out_before_any_violations():
    supplier_id = uuid.uuid4()

    assert abuse_tracking.is_locked_out(supplier_id) is False


def test_not_locked_out_below_the_threshold():
    supplier_id = uuid.uuid4()

    abuse_tracking.record_violation(supplier_id)
    abuse_tracking.record_violation(supplier_id)

    assert abuse_tracking.is_locked_out(supplier_id) is False


def test_locked_out_once_the_threshold_is_reached():
    supplier_id = uuid.uuid4()

    for _ in range(abuse_tracking.MAX_VIOLATIONS):
        abuse_tracking.record_violation(supplier_id)

    assert abuse_tracking.is_locked_out(supplier_id) is True


def test_violations_are_scoped_per_supplier_not_global():
    supplier_a = uuid.uuid4()
    supplier_b = uuid.uuid4()

    for _ in range(abuse_tracking.MAX_VIOLATIONS):
        abuse_tracking.record_violation(supplier_a)

    assert abuse_tracking.is_locked_out(supplier_a) is True
    assert abuse_tracking.is_locked_out(supplier_b) is False


def test_checking_lockout_status_never_increments_the_counter():
    """Read-only means read-only -- checking must never itself count
    as a violation, or every request would eventually lock everyone
    out just from being checked."""
    supplier_id = uuid.uuid4()
    abuse_tracking.record_violation(supplier_id)

    for _ in range(10):
        abuse_tracking.is_locked_out(supplier_id)

    assert abuse_tracking.is_locked_out(supplier_id) is False  # still just 1, not locked
