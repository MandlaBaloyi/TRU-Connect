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

    FOR A *MEASURED* SIZE, PREFER _as_base_quantity BELOW -- rejecting
    is only correct where there is no smaller unit to fall back on (a
    pack count has none; "2.5 x 6-pack" is not a thing).
    """
    cleaned = raw.replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return int(value) if value.is_integer() and value > 0 else None


def _as_base_quantity(raw: str, measure: str) -> tuple[Optional[int], Optional[str]]:
    """"2.5" + "KG" -> (2500, "G"). "5" + "KG" -> (5, "KG").

    WHY FRACTIONAL SIZES GET CONVERTED RATHER THAN DROPPED, and what it
    cost when they did not:

        "Ace Maize Meal 2.5kg" produced an EMPTY pack size, because 2.5
        is not an integer. The first supplier to list it therefore
        created a CATALOGUE ENTRY WITH NO PACK SIZE AT ALL -- from a
        name that visibly contains one.

        That entry then behaved as a magnet. _pack_agreement returns
        None, meaning "unknown", when either side has no base size, and
        unknown is correctly not treated as disagreement -- so the
        -0.40 penalty that exists for exactly this case never fired.
        "Ace Maize Meal 5kg" scored 1.0 against it instead of 0.65 and
        auto-linked. So did the 25kg.

        Measured on the seeded catalogue: one canonical product holding
        2.5kg, 5kg and 25kg maize meal from ten suppliers, R40.50 to
        R340.50, presented as alternatives to each other.

    THE CONVERSION LOSES NOTHING. ML and G are the base units this
    module already reduces everything to for comparison, and every
    fractional size a supplier writes is a whole number of them: 2.5kg
    is exactly 2500g, 1.5L is exactly 1500ml. to_base() already made
    5kg and 5000g compare equal, so storing the small unit changes no
    comparison -- it only stops a real size being thrown away.

    IT STILL REFUSES TO GUESS. A fraction with no smaller unit to
    express it in (2.5 of a bare count) returns None exactly as before,
    and so does anything that will not parse. The rule the module
    opened with holds: an unparsed size leaves the row for a later
    tier, a WRONG one silently corrupts a per-unit price.
    """
    cleaned = raw.replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        return None, None
    if value <= 0:
        return None, None

    if value.is_integer():
        return int(value), measure

    base_measure = _BASE_OF.get(measure)
    factor = _BASE_FACTORS.get(measure)
    if base_measure is None or factor is None or base_measure == measure:
        # Already the smallest unit we have, so there is nowhere to go:
        # "2.5ml" stays unparsed rather than becoming 2 or 3.
        return None, None

    in_base = value * factor
    if not float(in_base).is_integer():
        # Finer than the base unit (0.0005L). Real files do not contain
        # this; guessing at it is how a per-unit price goes wrong.
        return None, None
    return int(in_base), base_measure


def resolve_pack(pack: Optional["PackSize"], text: str | None) -> "PackSize":
    """The pack size to actually USE: what the caller supplied, or what
    the description says.

    ONE RULE, ONE PLACE, and it earned its own function the hard way.
    matching_service applied exactly this fallback when deciding a
    match, and linking_service did NOT when CREATING a product -- so a
    row matched on a size extracted from its name entered the catalogue
    with no size at all.

    Every such entry then behaved as a magnet: _pack_agreement reads a
    missing size as "unknown" rather than "different", which is correct,
    so the -0.40 penalty for a pack mismatch never fired against it.
    Measured on the seeded catalogue, one canonical product ended up
    holding 2.5kg, 5kg and 25kg maize meal from ten suppliers at
    R40.50 to R340.50, offered as alternatives to one another.

    Both callers now ask this, so the size a product is MATCHED on and
    the size it is STORED with cannot diverge again.
    """
    if pack is not None and not pack.is_empty:
        return pack
    return extract_pack_size(text)


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
        alias = MEASURE_ALIASES.get(measure_match.group(2).lower())
        # _as_base_quantity, NOT _as_int: a fractional size is expressed
        # in the base unit (2.5kg -> 2500 G) instead of being discarded.
        # Discarding it created catalogue entries with no pack size,
        # which then swallowed every other size of the same product --
        # see that function's docstring for the measured damage.
        quantity, resolved_measure = (
            _as_base_quantity(measure_match.group(1), alias) if alias else (None, None)
        )
        if quantity is not None and resolved_measure is not None:
            unit_quantity = quantity
            unit_measure = resolved_measure
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
