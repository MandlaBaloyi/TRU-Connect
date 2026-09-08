"""
Reading pack sizes out of the way suppliers actually write them.

"COKE 2LT PET 6PK" carries three facts -- 2 litres, six of them, and a
plastic bottle -- and none of them are in a column. This module gets the
first two out with regular expressions, for free, with no model call.

WHY RULES ARE THE RIGHT TOOL HERE, and not a fallback for lacking
something better: the vocabulary is tiny and repetitive. South African
FMCG suppliers write sizes perhaps a dozen ways, they abbreviate
consistently, and the same shorthand appears across thousands of rows.
That is precisely the shape of problem regular expressions are good at
and a language model is overkill for. Every format added here removes
rows from the AI tier permanently, so this file is where the matching
bill actually gets reduced.

WHAT IT DOES NOT DO. It does not guess. A description it cannot parse
returns empty rather than a probable answer, because an empty pack size
leaves a row for a later tier to handle, while a wrong one silently
corrupts a per-unit price -- and per-unit price is the number the whole
catalogue exists to make comparable.

BASE UNITS ARE THE POINT OF to_base(). "2L" and "2000ml" are the same
product and must compare equal; ML and G are the base for volume and
mass respectively, so both sides reduce to the same integer before
anything compares them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

#: Written form -> canonical ProductUnit value. Deliberately generous on
#: the left: these are the spellings that turn up in real files, not the
#: ones a style guide would prefer.
MEASURE_ALIASES = {
    "l": "L",
    "lt": "L",
    "ltr": "L",
    "litre": "L",
    "litres": "L",
    "liter": "L",
    "liters": "L",
    "ml": "ML",
    "mls": "ML",
    "millilitre": "ML",
    "kg": "KG",
    "kgs": "KG",
    "kilo": "KG",
    "kilos": "KG",
    "kilogram": "KG",
    "kilograms": "KG",
    "g": "G",
    "gr": "G",
    "gm": "G",
    "gms": "G",
    "gram": "G",
    "grams": "G",
}

#: How many of the base unit one of each measure is worth. ML for
#: volume, G for mass -- chosen because they are the SMALLEST, so every
#: conversion is a multiplication by an integer and nothing rounds.
_BASE_FACTORS = {"ML": 1, "L": 1000, "G": 1, "KG": 1000}
_BASE_OF = {"ML": "ML", "L": "ML", "G": "G", "KG": "G"}

_MEASURE_WORDS = "|".join(sorted(MEASURE_ALIASES, key=len, reverse=True))

#: "2lt", "750 ml", "1.5kg". Longest alias first (see _MEASURE_WORDS)
#: so "ml" never wins against "mls" and "l" never eats the "l" in "lt".
#:
#: THE LOOKBEHIND BLOCKS DIGITS ONLY, not letters, and that is
#: deliberate: in "12x500ml" the 500 is preceded by an "x". Blocking
#: letters too made that read as no size at all -- caught by a test,
#: which is exactly the case the pack-vs-size confusion turns on.
_MEASURE = re.compile(rf"(?<![0-9.])(\d+(?:[.,]\d+)?)\s*({_MEASURE_WORDS})(?![a-z])", re.I)

#: The many ways "six of them" gets written. Each alternative captures
#: the count in its own group; the first that matches wins.
_PACK_PATTERNS = (
    re.compile(r"(?<![a-z0-9])x\s*(\d+)(?![a-z0-9])", re.I),            # x6, x 6
    re.compile(r"(?<![a-z0-9])(\d+)\s*x(?![a-z0-9])", re.I),            # 6x, 6 x
    re.compile(r"(?<![a-z0-9])(\d+)\s*(?:pk|pack|packs)(?![a-z])", re.I),  # 6pk, 6 pack
    re.compile(r"(?<![a-z0-9])(?:pk|pack)\s*(\d+)(?![a-z0-9])", re.I),  # pk6
    re.compile(r"case\s*of\s*(\d+)(?![a-z0-9])", re.I),                  # case of 6
    re.compile(r"box\s*of\s*(\d+)(?![a-z0-9])", re.I),                   # box of 6
    re.compile(r"(?<![a-z0-9])(\d+)\s*(?:'s|s)(?=\s|$)", re.I),          # 6's, 6s
)


@dataclass(frozen=True)
class PackSize:
    """What was readable in the text. Every field optional, because
    partial information is normal and useful: "6 pack" with no size
    still narrows candidates."""

    #: The CONSUMER unit: 2 for "2L", 750 for "750ml".
    unit_quantity: Optional[int] = None
    #: A ProductUnit value: "L", "ML", "KG", "G".
    unit_measure: Optional[str] = None
    #: How many consumer units in the pack: 6 for "6PK".
    pack_quantity: Optional[int] = None

    @property
    def is_empty(self) -> bool:
        return (
            self.unit_quantity is None
            and self.unit_measure is None
            and self.pack_quantity is None
        )

    def to_base(self) -> Optional[int]:
        """The consumer unit in ML or G, so 2L and 2000ml compare equal.

        None when there is no measured size -- which is not a failure.
        Plenty of real products ("Bread White", "Building Sand") have no
        measure at all.
        """
        if self.unit_quantity is None or self.unit_measure is None:
            return None
        factor = _BASE_FACTORS.get(self.unit_measure)
        return None if factor is None else self.unit_quantity * factor

    @property
    def base_measure(self) -> Optional[str]:
        """"ML" or "G" -- what to_base() is counted in."""
        return _BASE_OF.get(self.unit_measure) if self.unit_measure else None


def _as_int(raw: str) -> Optional[int]:
    """"1.5" -> None, "2" -> 2, "2,0" -> 2.

    FRACTIONAL SIZES ARE REJECTED RATHER THAN ROUNDED. unit_quantity is
    an integer column, and 1.5kg silently becoming 1kg or 2kg would put
    a wrong per-unit price on a product card. Returning None sends the
    row to a later tier, which is the honest outcome.
    """
    cleaned = raw.replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return int(value) if value.is_integer() and value > 0 else None


def extract_pack_size(text: str | None) -> PackSize:
    """Read whatever size information the text contains.

    THE MEASURE IS FOUND FIRST, AND ITS DIGITS ARE THEN HIDDEN from the
    pack search. Without that, "12x500ml" would let the pack patterns
    see the 500 and the 12 and pick whichever matched first. Blanking
    the measure leaves "12x", which is unambiguous.
    """
    if not text:
        return PackSize()

    unit_quantity: Optional[int] = None
    unit_measure: Optional[str] = None

    remainder = text
    measure_match = _MEASURE.search(text)
    if measure_match:
        quantity = _as_int(measure_match.group(1))
        alias = MEASURE_ALIASES.get(measure_match.group(2).lower())
        if quantity is not None and alias is not None:
            unit_quantity = quantity
            unit_measure = alias
            # Blank out what we just consumed so the pack search cannot
            # mistake the size for a count.
            remainder = text[: measure_match.start()] + " " + text[measure_match.end() :]

    pack_quantity: Optional[int] = None
    for pattern in _PACK_PATTERNS:
        found = pattern.search(remainder)
        if found:
            candidate = _as_int(found.group(1))
            # A "pack of 1" is not a pack. Treating it as one would put
            # "1 x" on a product card and change nothing else.
            if candidate is not None and candidate > 1:
                pack_quantity = candidate
            break

    return PackSize(
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
        pack_quantity=pack_quantity,
    )
