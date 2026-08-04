"""
Parsing -- human-entered text to Money.

This is the ONLY place in the platform allowed to interpret messy human
input as an amount. Everything downstream receives an exact Money or an
error, never a "probably right" number.

Handles what South African users actually type: "R500", "r 500,50"
(comma as decimal separator is common), "1 250.00", "1,250.50", with
stray spaces and non-breaking spaces from copy-paste.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from src.shared.finance.core.currency import DEFAULT_CURRENCY, Currency
from src.shared.finance.core.exceptions import ParseError
from src.shared.finance.core.money import Money

_CURRENCY_PREFIX = re.compile(r"^\s*[A-Za-z$£€¥]{0,3}\s*")
_ALLOWED_CHARS = re.compile(r"^-?[\d.,\s\u00a0]+$")


def parse_amount(text: str, currency: Currency = DEFAULT_CURRENCY) -> Money:
    """
    parse_amount("R 1 250,50") -> Money(125050, ZAR)

    Raises ParseError rather than guessing on anything ambiguous -- a
    silently misparsed amount is far worse than asking the user again.
    """
    if text is None:
        raise ParseError("No amount provided")
    if not isinstance(text, str):
        raise ParseError(f"Expected text, got {type(text).__name__}")

    working = text.strip()

    # The sign is stripped BEFORE the currency prefix, because people
    # type "-R500", not "R-500" -- handling the prefix first would leave
    # a stranded "-" that fails the allowed-characters check. Both
    # orderings are accepted below for safety.
    negative = False
    if working.startswith("-"):
        negative = True
        working = working[1:].strip()

    cleaned = _CURRENCY_PREFIX.sub("", working, count=1).strip()

    if cleaned.startswith("-"):  # handles the "R-500" ordering too
        negative = True
        cleaned = cleaned[1:].strip()

    if not cleaned:
        raise ParseError(f"Could not read an amount from {text!r}")
    if not _ALLOWED_CHARS.match(cleaned):
        raise ParseError(f"Could not read an amount from {text!r}")

    # Strip spaces (including non-breaking) used as thousands separators.
    cleaned = cleaned.replace("\u00a0", "").replace(" ", "")

    normalised = _normalise_separators(cleaned, text)

    try:
        value = Decimal(normalised)
    except InvalidOperation:
        raise ParseError(f"Could not read an amount from {text!r}") from None

    if negative:
        value = -value

    scaled = value * currency.subunit_factor
    if scaled != scaled.to_integral_value():
        raise ParseError(
            f"{text!r} has more decimal places than {currency.code} supports "
            f"({currency.minor_units})."
        )

    return Money(int(scaled), currency)


def _normalise_separators(cleaned: str, original: str) -> str:
    """
    Work out which of '.' and ',' is the decimal separator.

    Both appear in real South African input -- "1,250.50" (comma =
    thousands) and "1250,50" (comma = decimal) are both things people
    type. Guessing wrong turns R1 250.50 into R125 050, so anything
    genuinely ambiguous raises instead.
    """
    has_dot = "." in cleaned
    has_comma = "," in cleaned

    if has_dot and has_comma:
        # Whichever appears LAST is the decimal separator; the other is
        # grouping. "1,250.50" -> dot decimal. "1.250,50" -> comma decimal.
        if cleaned.rfind(".") > cleaned.rfind(","):
            return cleaned.replace(",", "")
        return cleaned.replace(".", "").replace(",", ".")

    if has_comma:
        # A single comma with 1-2 trailing digits is a decimal separator
        # ("500,50"); anything else is grouping ("1,250").
        before, _, after = cleaned.rpartition(",")
        if before and 1 <= len(after) <= 2 and after.isdigit():
            return f"{before}.{after}"
        return cleaned.replace(",", "")

    if cleaned.count(".") > 1:
        raise ParseError(f"Could not read an amount from {original!r}")

    return cleaned
