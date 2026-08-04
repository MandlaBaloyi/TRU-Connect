"""
Formatting -- Money to human-readable text. Display only; never
arithmetic.

Derives decimal places from the currency's own minor_units rather than
assuming 2, so JPY renders as "¥1250" (no decimals) and BHD as
"BD 1.250" (three) without any special-casing at the call site.

South African convention by default: a space as the thousands separator
("R 1 250.00"), not a comma. Uses a NON-BREAKING space specifically so a
displayed amount can never wrap across two lines mid-number, which would
be both ugly and briefly misreadable.
"""

from __future__ import annotations

from decimal import Decimal

from src.shared.finance.core.constants import (
    DEFAULT_DECIMAL_SEPARATOR,
    DEFAULT_THOUSANDS_SEPARATOR,
)
from src.shared.finance.core.money import Money


def format_amount(
    amount: Money,
    *,
    with_symbol: bool = True,
    thousands_separator: str = DEFAULT_THOUSANDS_SEPARATOR,
    decimal_separator: str = DEFAULT_DECIMAL_SEPARATOR,
) -> str:
    """
    format_amount(Money(125050))  ->  "R 1 250.50"
    format_amount(Money(1250, JPY)) -> "¥1250"
    """
    currency = amount.currency
    negative = amount.minor_units < 0
    units = abs(amount.minor_units)

    factor = currency.subunit_factor
    whole = units // factor
    fraction = units % factor

    # Zero-decimal currencies (JPY) conventionally render without a
    # thousands separator in compact UI contexts; keeping the separator
    # only where the currency actually subdivides avoids "¥1 250"
    # reading as though 250 were a fractional part.
    grouped = _group_thousands(whole, thousands_separator) if currency.minor_units > 0 else str(whole)

    if currency.minor_units > 0:
        fraction_text = str(fraction).rjust(currency.minor_units, "0")
        body = f"{grouped}{decimal_separator}{fraction_text}"
    else:
        body = grouped

    if with_symbol:
        # ZAR convention puts a space after the symbol ("R 1 250.00");
        # JPY/USD conventionally don't ("¥1250", "$12.50").
        gap = " " if currency.code == "ZAR" else ""
        body = f"{currency.symbol}{gap}{body}"

    return f"-{body}" if negative else body


def format_compact(amount: Money) -> str:
    """
    Shorter form for tight spaces (chips, badges): drops the fractional
    part when it's zero. Money(50000) -> "R 500", Money(50050) -> "R 500.50".
    """
    if amount.currency.minor_units > 0 and amount.minor_units % amount.currency.subunit_factor == 0:
        whole = abs(amount.minor_units) // amount.currency.subunit_factor
        grouped = _group_thousands(whole, DEFAULT_THOUSANDS_SEPARATOR)
        gap = " " if amount.currency.code == "ZAR" else ""
        sign = "-" if amount.minor_units < 0 else ""
        return f"{sign}{amount.currency.symbol}{gap}{grouped}"
    return format_amount(amount)


def format_for_json(amount: Money) -> dict:
    """
    The API representation.

    Uses the field name `amount_cents`-style explicitness (`minor_units`
    plus an explicit `currency`) rather than a bare `amount`, so nobody
    reading an API response has to guess whether 50000 means R500.00 or
    R50 000. That one naming decision removes an entire class of bug.

    `formatted` is included for convenience but is NEVER the source of
    truth -- clients must calculate from minor_units, never parse the
    display string.
    """
    return {
        "minor_units": amount.minor_units,
        "currency": amount.currency.code,
        "formatted": format_amount(amount),
    }


def _group_thousands(value: int, separator: str) -> str:
    text = str(value)
    if len(text) <= 3:
        return text
    chunks = []
    while len(text) > 3:
        chunks.insert(0, text[-3:])
        text = text[:-3]
    chunks.insert(0, text)
    return separator.join(chunks)
