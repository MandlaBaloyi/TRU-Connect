"""
Allocation -- the cent-loss guarantees.

These are the highest-value tests in the engine: a bug here doesn't
crash, it silently loses money.
"""

from __future__ import annotations

import pytest

from src.shared.finance.core.allocation import (
    allocate_to_debts,
    split_by_ratios,
    split_evenly,
    unallocated_remainder,
)
from src.shared.finance.core.exceptions import AllocationError
from src.shared.finance.core.money import Money


@pytest.mark.parametrize("amount,parts", [
    (10000, 3), (100, 3), (1, 3), (0, 3), (99999, 7), (33333, 11), (5, 100),
])
def test_split_evenly_never_loses_a_minor_unit(amount, parts):
    result = split_evenly(Money(amount), parts)
    assert sum(m.minor_units for m in result) == amount
    assert len(result) == parts


def test_split_evenly_r100_three_ways():
    """The canonical example: naive division gives 9999, not 10000."""
    assert [m.minor_units for m in split_evenly(Money(10000), 3)] == [3334, 3333, 3333]


@pytest.mark.parametrize("amount,ratios", [
    (10000, [1, 1, 1]), (10000, [1, 2, 3]), (100, [1, 1, 1]),
    (1, [1, 1, 1]), (33333, [7, 11, 13]), (12345, [1]), (99, [50, 50]),
])
def test_split_by_ratios_never_loses_a_minor_unit(amount, ratios):
    result = split_by_ratios(Money(amount), ratios)
    assert sum(m.minor_units for m in result) == amount


def test_split_by_ratios_is_deterministic():
    """Same inputs must always give the same split -- required for
    reproducibility and for tests to mean anything."""
    a = [m.minor_units for m in split_by_ratios(Money(10000), [1, 1, 1])]
    b = [m.minor_units for m in split_by_ratios(Money(10000), [1, 1, 1])]
    assert a == b


def test_split_by_ratios_rejects_floats():
    with pytest.raises(TypeError):
        split_by_ratios(Money(10000), [0.5, 0.5])


def test_split_rejects_invalid_parts():
    with pytest.raises(AllocationError):
        split_evenly(Money(100), 0)
    with pytest.raises(AllocationError):
        split_by_ratios(Money(100), [0, 0])


def test_allocate_to_debts_fifo():
    """The Loan Book case: R200 across a R10 and a R500 debt."""
    debts = [Money(1000), Money(50000)]
    assert [m.minor_units for m in allocate_to_debts(Money(20000), debts)] == [1000, 19000]


def test_allocate_never_exceeds_debt():
    debts = [Money(1000), Money(50000)]
    allocations = allocate_to_debts(Money(100000), debts)
    assert [m.minor_units for m in allocations] == [1000, 50000]
    assert unallocated_remainder(Money(100000), debts).minor_units == 49000


def test_allocate_partial_payment():
    debts = [Money(50000)]
    assert [m.minor_units for m in allocate_to_debts(Money(20000), debts)] == [20000]


def test_allocate_rejects_negative_payment():
    with pytest.raises(Exception):
        allocate_to_debts(Money(-100), [Money(1000)])
