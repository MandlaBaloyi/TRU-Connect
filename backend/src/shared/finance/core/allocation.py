"""
Allocation -- splitting money between parts, and applying payments
across debts.

THE CENT-LOSS PROBLEM THIS SOLVES:
Splitting R100 three ways naively gives R33.33 each, totalling R99.99 --
one cent has vanished. Do that across thousands of transactions and the
platform's books genuinely don't balance. The "largest remainder" method
below guarantees the parts ALWAYS sum back to exactly the original
amount, by distributing the leftover minor units one at a time to
whichever parts were rounded down hardest.

This is a solved problem in finance, implemented here once so no feature
has to solve it again (or, worse, solve it slightly differently).
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Sequence, Union

from src.shared.finance.core.exceptions import AllocationError
from src.shared.finance.core.money import Money


def split_evenly(amount: Money, parts: int) -> List[Money]:
    """
    Split into `parts` as evenly as possible, with the remainder
    distributed one minor unit at a time from the first part onward.

    split_evenly(Money(10000), 3) -> [3334, 3333, 3333] cents,
    which sums to exactly 10000 -- never 9999.
    """
    if parts <= 0:
        raise AllocationError(f"Cannot split into {parts} parts; must be >= 1")

    base, remainder = divmod(amount.minor_units, parts)
    result = []
    for index in range(parts):
        extra = 1 if index < remainder else 0
        result.append(Money(base + extra, amount.currency))
    return result


def split_by_ratios(amount: Money, ratios: Sequence[Union[int, str, Decimal]]) -> List[Money]:
    """
    Split proportionally by weights, using the largest-remainder method
    so the parts sum EXACTLY to `amount`.

    Each part is first floored to a whole minor unit, then the leftover
    units are handed out to whichever parts lost the most to flooring --
    that's what makes the total exact rather than approximately right.

    split_by_ratios(Money(10000), [1, 1, 1]) -> [3334, 3333, 3333]
    """
    if not ratios:
        raise AllocationError("split_by_ratios requires at least one ratio")
    if any(isinstance(r, float) for r in ratios):
        raise TypeError("split_by_ratios rejects float ratios -- pass int, str, or Decimal.")

    decimal_ratios = [Decimal(r) for r in ratios]
    if any(r < 0 for r in decimal_ratios):
        raise AllocationError("Ratios must not be negative")

    ratio_total = sum(decimal_ratios)
    if ratio_total == 0:
        raise AllocationError("Ratios must not all be zero")

    # Floor each share, and remember how much each one lost to flooring.
    exact_shares = [Decimal(amount.minor_units) * r / ratio_total for r in decimal_ratios]
    floored = [int(share // 1) for share in exact_shares]
    remainders = [share - floor for share, floor in zip(exact_shares, floored)]

    leftover = amount.minor_units - sum(floored)

    # Hand the leftover units to the biggest losers first. Ties break by
    # original index, so the result is deterministic -- the same inputs
    # always produce the same split, which matters for reproducibility
    # and for tests.
    order = sorted(range(len(remainders)), key=lambda i: (-remainders[i], i))
    for offset in range(leftover):
        floored[order[offset % len(order)]] += 1

    return [Money(units, amount.currency) for units in floored]


def allocate_to_debts(payment: Money, debts: Sequence[Money]) -> List[Money]:
    """
    Apply a payment across outstanding debts in the order given
    (oldest-first / FIFO is the caller's responsibility to order).

    Returns how much lands on each debt, in the same order. If the
    payment exceeds the total owed, the excess is simply not allocated --
    this function never returns more than each debt is owed, and never
    invents an over-payment. The caller decides what an unallocated
    remainder means (change owed, credit balance, rejection).
    """
    payment.require_non_negative()
    remaining = payment
    allocations: List[Money] = []

    for debt in debts:
        debt._assert_same_currency(payment)
        if debt.is_negative:
            raise AllocationError(f"Cannot allocate against a negative debt: {debt}")
        take = min(remaining.minor_units, debt.minor_units)
        allocations.append(Money(take, payment.currency))
        remaining = Money(remaining.minor_units - take, payment.currency)

    return allocations


def unallocated_remainder(payment: Money, debts: Sequence[Money]) -> Money:
    """How much of `payment` is left over after allocate_to_debts()."""
    allocated = sum(a.minor_units for a in allocate_to_debts(payment, debts))
    return Money(payment.minor_units - allocated, payment.currency)
