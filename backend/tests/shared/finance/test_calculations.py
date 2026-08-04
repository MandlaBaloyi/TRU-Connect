"""Arithmetic, rounding, and validation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.shared.finance.core import calculations as calc
from src.shared.finance.core.currency import USD, ZAR
from src.shared.finance.core.exceptions import CurrencyMismatchError
from src.shared.finance.core.money import Money
from src.shared.finance.core.rounding import RoundingMode, round_to_minor_units
from src.shared.finance.core.validation import (
    validate_non_negative,
    validate_payment,
    validate_positive,
    validate_within,
)


def test_basic_arithmetic():
    assert calc.add(Money(5000), Money(2500)).minor_units == 7500
    assert calc.subtract(Money(5000), Money(2500)).minor_units == 2500
    assert calc.negate(Money(5000)).minor_units == -5000
    assert calc.absolute(Money(-5000)).minor_units == 5000


def test_subtract_may_go_negative():
    """Reversals and corrections legitimately need negatives; the engine
    doesn't ban them, callers opt in to requiring non-negativity."""
    assert calc.subtract(Money(100), Money(500)).minor_units == -400


def test_arithmetic_rejects_currency_mismatch():
    with pytest.raises(CurrencyMismatchError):
        calc.add(Money(100, ZAR), Money(100, USD))


def test_total_of_empty_is_zero():
    assert calc.total([]).minor_units == 0


def test_total_sums_correctly():
    assert calc.total([Money(100), Money(250), Money(50)]).minor_units == 400


def test_multiply_and_percentage_reject_floats():
    with pytest.raises(TypeError):
        calc.multiply(Money(10000), 1.5)
    with pytest.raises(TypeError):
        calc.percentage(Money(10000), 15.0)


def test_percentage_vat_example():
    assert calc.percentage(Money(10000), "15").minor_units == 1500


def test_multiply_rounds_to_whole_minor_units():
    """A third of a cent cannot be owed, paid, or stored."""
    assert calc.multiply(Money(10), "0.35").minor_units == 4  # 3.5 -> 4 HALF_UP


def test_rounding_modes_differ_predictably():
    assert round_to_minor_units(Decimal("2.5"), RoundingMode.HALF_UP) == 3
    assert round_to_minor_units(Decimal("2.5"), RoundingMode.HALF_EVEN) == 2
    assert round_to_minor_units(Decimal("2.9"), RoundingMode.DOWN) == 2
    assert round_to_minor_units(Decimal("2.1"), RoundingMode.UP) == 3


def test_rounding_rejects_float():
    with pytest.raises(TypeError):
        round_to_minor_units(2.5)


def test_min_max():
    assert calc.min_of(Money(100), Money(500)).minor_units == 100
    assert calc.max_of(Money(100), Money(500)).minor_units == 500


def test_validation_returns_results_not_exceptions():
    """User-input failures are routine, not exceptional."""
    assert validate_positive(Money(100)).is_valid
    assert not validate_positive(Money(0)).is_valid
    assert not validate_positive(Money(-1)).is_valid
    assert validate_non_negative(Money(0)).is_valid


def test_validate_within_message_is_plain_language():
    result = validate_within(Money(60000), Money(50000))
    assert not result.is_valid
    assert "R 500.00" in result.message
    assert "more than" in result.message.lower()


def test_validate_payment_combines_rules():
    assert validate_payment(Money(20000), Money(50000)).is_valid
    assert not validate_payment(Money(0), Money(50000)).is_valid       # not positive
    assert not validate_payment(Money(60000), Money(50000)).is_valid   # exceeds debt
