"""Formatting and parsing -- including the round-trip property."""

from __future__ import annotations

import pytest

from src.shared.finance.core.currency import BHD, JPY, USD, ZAR
from src.shared.finance.core.exceptions import ParseError
from src.shared.finance.core.formatter import format_amount, format_compact, format_for_json
from src.shared.finance.core.money import Money
from src.shared.finance.core.parser import parse_amount

NBSP = "\u00a0"


def test_zar_formatting():
    assert format_amount(Money(125050)) == f"R 1{NBSP}250.50"
    assert format_amount(Money(50000)) == "R 500.00"
    assert format_amount(Money(5)) == "R 0.05"
    assert format_amount(Money(0)) == "R 0.00"
    assert format_amount(Money(-125050)) == f"-R 1{NBSP}250.50"


def test_formatting_respects_currency_minor_units():
    assert format_amount(Money(1250, JPY)) == "¥1250"       # 0 dp
    assert format_amount(Money(1250, BHD)) == "BD1.250"     # 3 dp
    assert format_amount(Money(1250, USD)) == "$12.50"      # 2 dp


def test_compact_drops_zero_fraction():
    assert format_compact(Money(50000)) == "R 500"
    assert format_compact(Money(50050)) == "R 500.50"


@pytest.mark.parametrize("text,expected", [
    ("R500", 50000),
    ("R 500.50", 50050),
    ("r500,50", 50050),          # comma as decimal separator
    ("1 250.00", 125000),        # space as thousands separator
    ("1,250.50", 125050),        # comma as thousands, dot as decimal
    ("1.250,50", 125050),        # dot as thousands, comma as decimal
    ("500", 50000),
    ("0.01", 1),
    ("-R500.00", -50000),
    ("R-500", -50000),
])
def test_parses_real_south_african_input(text, expected):
    assert parse_amount(text).minor_units == expected


@pytest.mark.parametrize("bad", ["", "abc", "R", "1.2.3", "500.555", None, "12abc", 123])
def test_rejects_unparseable_input(bad):
    with pytest.raises(ParseError):
        parse_amount(bad)


@pytest.mark.parametrize("text", ["R 1 250.50", "R500", "0.01", "-R500.00", "1234567.89"])
def test_parse_format_round_trip_is_stable(text):
    """format(parse(x)) must re-parse to the same value -- otherwise a
    displayed amount can't be trusted as an input elsewhere."""
    first = parse_amount(text)
    assert parse_amount(format_amount(first)).minor_units == first.minor_units


def test_json_shape_is_explicit_about_units():
    """`minor_units` + `currency`, never a bare `amount` -- so nobody
    reading an API response has to guess whether 50000 is R500 or R50000."""
    payload = format_for_json(Money(125050))
    assert payload["minor_units"] == 125050
    assert payload["currency"] == "ZAR"
    assert "formatted" in payload
