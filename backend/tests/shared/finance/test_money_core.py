"""Core Money value object -- construction, precision, rejections."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.shared.finance.core.currency import BHD, JPY, USD, ZAR, get_currency
from src.shared.finance.core.exceptions import (
    CurrencyMismatchError,
    InvalidAmountError,
    MoneyOverflowError,
    NegativeAmountError,
    UnknownCurrencyError,
)
from src.shared.finance.core.money import Money


def test_money_is_integer_minor_units():
    assert Money(50000).minor_units == 50000
    assert Money(50000).to_major_units() == Decimal("500")


@pytest.mark.parametrize("bad", [12.5, 0.1, True, False, "500", None])
def test_rejects_non_integer_minor_units(bad):
    with pytest.raises(InvalidAmountError):
        Money(bad)


def test_from_major_units_respects_currency_precision():
    """The whole point of minor_units living on Currency."""
    assert Money.from_major_units("12.50", ZAR).minor_units == 1250   # 2 dp
    assert Money.from_major_units("1250", JPY).minor_units == 1250    # 0 dp
    assert Money.from_major_units("1.250", BHD).minor_units == 1250   # 3 dp


def test_from_major_units_rejects_float():
    with pytest.raises(InvalidAmountError):
        Money.from_major_units(12.50, ZAR)


def test_from_major_units_rejects_excess_precision():
    with pytest.raises(InvalidAmountError):
        Money.from_major_units("12.505", ZAR)  # ZAR has only 2 dp


def test_jpy_has_no_subunit_division():
    """Guards against a /100 assumption leaking in anywhere."""
    assert Money(1250, JPY).to_major_units() == Decimal("1250")


def test_overflow_is_rejected_at_js_safe_integer_boundary():
    Money(2**53 - 1)  # fine
    with pytest.raises(MoneyOverflowError):
        Money(2**53)


def test_cross_currency_comparison_raises():
    with pytest.raises(CurrencyMismatchError):
        Money(100, ZAR) < Money(100, USD)


def test_money_is_immutable():
    m = Money(100)
    with pytest.raises(Exception):
        m.minor_units = 200  # frozen dataclass


def test_require_non_negative():
    Money(0).require_non_negative()
    Money(100).require_non_negative()
    with pytest.raises(NegativeAmountError):
        Money(-1).require_non_negative()


def test_currency_lookup():
    assert get_currency("zar") is ZAR
    with pytest.raises(UnknownCurrencyError):
        get_currency("XXX")
