"""
Rounding strategies.

Every rounding decision in the platform goes through here, so the answer
to "how does TRU Connect round?" is one file, not scattered per-feature
guesses that quietly disagree with each other.

Uses Python's `decimal` module rather than round()/float arithmetic:
Python's built-in round() uses banker's rounding on floats and inherits
every float precision problem, which is exactly what this engine exists
to avoid.
"""

from __future__ import annotations

import enum
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP, Decimal


class RoundingMode(str, enum.Enum):
    """
    HALF_UP -- 0.5 rounds away from zero (2.5 -> 3). What most people
        intuitively expect, and what South African retail pricing
        conventions assume. The engine default.

    HALF_EVEN -- 0.5 rounds to the nearest even digit (2.5 -> 2,
        3.5 -> 4), a.k.a. banker's rounding. Statistically unbiased
        across many roundings, which is why accounting systems often
        prefer it. Available deliberately, not the default, because it
        surprises people who expect 2.5 -> 3.

    DOWN / UP -- always toward/away from zero. Used for specific rules
        (e.g. never charging a fraction more than earned), not general
        arithmetic.
    """

    HALF_UP = "half_up"
    HALF_EVEN = "half_even"
    DOWN = "down"
    UP = "up"


_DECIMAL_MODES = {
    RoundingMode.HALF_UP: ROUND_HALF_UP,
    RoundingMode.HALF_EVEN: ROUND_HALF_EVEN,
    RoundingMode.DOWN: ROUND_DOWN,
    RoundingMode.UP: ROUND_UP,
}

DEFAULT_ROUNDING = RoundingMode.HALF_UP


def round_to_minor_units(value: Decimal, mode: RoundingMode = DEFAULT_ROUNDING) -> int:
    """
    Round an exact Decimal to a whole number of minor units.

    Takes Decimal (not float) on purpose -- accepting a float here would
    let an already-imprecise value in through the one door specifically
    built to keep imprecision out.
    """
    if not isinstance(value, Decimal):
        raise TypeError(
            f"round_to_minor_units expects Decimal, got {type(value).__name__}. "
            f"Floats are rejected on purpose -- see this module's docstring."
        )
    return int(value.quantize(Decimal(1), rounding=_DECIMAL_MODES[mode]))
