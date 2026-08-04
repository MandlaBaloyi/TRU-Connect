"""
Money arithmetic. Every add/subtract/multiply in the platform goes
through here.

WHY THESE ARE FUNCTIONS, NOT `__add__`/`__sub__` OPERATORS ON Money:
operators would let `total = a + b` appear anywhere, including inside a
domain that then quietly grows its own money logic around it. Explicit
`add(a, b)` calls keep every arithmetic site greppable and make the
"no feature performs its own calculations" rule verifiable rather than
merely stated.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Union

from src.shared.finance.core.currency import DEFAULT_CURRENCY, Currency
from src.shared.finance.core.exceptions import CurrencyMismatchError
from src.shared.finance.core.money import Money
from src.shared.finance.core.rounding import DEFAULT_ROUNDING, RoundingMode, round_to_minor_units


def add(a: Money, b: Money) -> Money:
    a._assert_same_currency(b)
    return Money(a.minor_units + b.minor_units, a.currency)


def subtract(a: Money, b: Money) -> Money:
    """a - b. May return a negative Money; callers requiring
    non-negativity should follow with .require_non_negative()."""
    a._assert_same_currency(b)
    return Money(a.minor_units - b.minor_units, a.currency)


def negate(a: Money) -> Money:
    return Money(-a.minor_units, a.currency)


def absolute(a: Money) -> Money:
    return Money(abs(a.minor_units), a.currency)


def total(amounts: Iterable[Money], currency: Currency = DEFAULT_CURRENCY) -> Money:
    """
    Sum any iterable of Money.

    `currency` is only used for the EMPTY case (so summing nothing still
    returns a correctly-typed zero rather than failing) -- when amounts
    are present, their own currency wins, and a mismatch against
    `currency` raises rather than being silently coerced.
    """
    running = Money.zero(currency)
    first = True
    for amount in amounts:
        if first:
            running = Money.zero(amount.currency)
            if amount.currency.code != currency.code and currency is not DEFAULT_CURRENCY:
                raise CurrencyMismatchError(
                    f"total() was told {currency.code} but received {amount.currency.code}"
                )
            first = False
        running = add(running, amount)
    return running


def multiply(
    amount: Money,
    factor: Union[int, str, Decimal],
    rounding: RoundingMode = DEFAULT_ROUNDING,
) -> Money:
    """
    Multiply by a scalar (e.g. quantity, or a rate like '0.15' for VAT).

    Rejects float factors for the same reason Money rejects float
    amounts: 0.1 as a float is not exactly 0.1, and multiplying an exact
    amount by an inexact factor produces an inexact result while looking
    perfectly reasonable. Pass '0.15' or Decimal('0.15').

    The result is rounded to whole minor units, since a fraction of a
    cent cannot be stored, paid, or owed.
    """
    if isinstance(factor, float):
        raise TypeError(
            "multiply() rejects float factors -- pass a str or Decimal "
            "(e.g. '0.15'). See this module's docstring."
        )
    exact = Decimal(amount.minor_units) * Decimal(factor)
    return Money(round_to_minor_units(exact, rounding), amount.currency)


def percentage(
    amount: Money,
    percent: Union[int, str, Decimal],
    rounding: RoundingMode = DEFAULT_ROUNDING,
) -> Money:
    """percent% of amount. percentage(Money(10000), '15') -> R15.00 of R100.00."""
    if isinstance(percent, float):
        raise TypeError("percentage() rejects float -- pass a str or Decimal (e.g. '15').")
    return multiply(amount, Decimal(percent) / Decimal(100), rounding)


def is_greater(a: Money, b: Money) -> bool:
    return a > b


def is_less(a: Money, b: Money) -> bool:
    return a < b


def min_of(a: Money, b: Money) -> Money:
    a._assert_same_currency(b)
    return a if a <= b else b


def max_of(a: Money, b: Money) -> Money:
    a._assert_same_currency(b)
    return a if a >= b else b
