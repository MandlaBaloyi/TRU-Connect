"""
GTIN validation -- the check digit that makes tier 0 safe to trust.

THE PROBLEM THIS EXISTS FOR, asked plainly during review: what happens
if a supplier types one digit of a barcode wrong?

Before this module: nothing good. The import validator accepted any run
of 8 to 14 digits, and matching_service handed it straight to
get_by_gtin() as tier 0 -- the tier whose whole justification is that a
barcode is EXACT. A single mistyped digit could therefore do one of two
things, and the second is the dangerous one:

  · match nothing, and quietly fall through to the fuzzy tiers. Mildly
    wasteful, harmless.

  · match A DIFFERENT REAL PRODUCT. Barcodes are densely allocated
    within a manufacturer's range, so a one-digit slip on a live GTIN
    frequently lands on another live GTIN -- often from the same
    manufacturer, which is exactly the case where the names look
    plausible enough that nobody notices. The supplier's 2L cooldrink
    becomes the catalogue's 500ml, at tier 0, with confidence 1.0 and
    the reason "Barcode matches this product exactly."

That is the worst failure mode the matching ladder can produce: a
confident, unreviewable, wrong link, on the tier nobody thinks to
question.

WHY A CHECK DIGIT FIXES IT. Every GTIN (GTIN-8, GTIN-12/UPC-A,
GTIN-13/EAN-13, GTIN-14) reserves its last digit as a checksum over the
others, weighted alternately 3 and 1 from the right. That scheme is
specifically designed to catch the two errors humans actually make:

  · ANY single-digit substitution -- caught, always, 100%.
  · Most adjacent transpositions ("...34..." typed as "...43...").
    Caught unless the two digits differ by exactly 5, which is the one
    documented blind spot of the standard and not something we can fix.

So a mistyped barcode now fails here, loudly, at the row it came from,
instead of silently becoming a wrong product months later.

WHAT WE DO WITH A FAILURE, and this is a product decision rather than a
technical one: the row is NOT rejected. A bad barcode is not a bad
product -- the name, price and pack size are all still perfectly good.
The barcode is dropped, the supplier is told which row and which value,
and the row proceeds through the remaining tiers on its text. Refusing
the whole row would punish a supplier for a typo in an OPTIONAL column,
which is the fastest way to teach them to stop filling it in -- and
that column is the single most valuable one in the file.
"""
from __future__ import annotations

from typing import Optional

# GTIN-8, GTIN-12 (UPC-A), GTIN-13 (EAN-13), GTIN-14 (case/carton).
#
# NOTHING ELSE IS A GTIN. The import validator's old rule -- "8 to 14
# digits" -- also admitted 9, 10 and 11, which are not GTINs of any
# kind and cannot have a valid check digit. They were being accepted
# and then failing to match anything, forever.
VALID_GTIN_LENGTHS = (8, 12, 13, 14)


def check_digit(payload: str) -> int:
    """The check digit for a GTIN body (everything but the last digit).

    Weights alternate 3, 1 starting from the RIGHTMOST digit of the
    payload -- which is why this works unchanged for all four lengths
    rather than needing a table per format.
    """
    total = 0
    for index, character in enumerate(reversed(payload)):
        total += int(character) * (3 if index % 2 == 0 else 1)
    return (10 - (total % 10)) % 10


def is_valid_gtin(value: Optional[str]) -> bool:
    """True only for a digit string of a real GTIN length whose check
    digit agrees.

    Deliberately strict and deliberately silent -- it answers one
    question and raises nothing, so callers can use it in a condition.
    """
    if not value or not value.isdigit():
        return False
    if len(value) not in VALID_GTIN_LENGTHS:
        return False
    return int(value[-1]) == check_digit(value[:-1])


def normalise_gtin(value: Optional[str]) -> Optional[str]:
    """Returns the GTIN if it is valid, otherwise None.

    THE CONVENIENCE THAT KEEPS CALLERS HONEST. Every caller wants "give
    me a barcode I can trust or give me nothing", and returning None
    rather than the invalid string means a caller that forgets to check
    gets no barcode instead of a bad one. The failure mode of
    forgetting is then a missed match, never a wrong one.
    """
    return value if is_valid_gtin(value) else None


# ---------------------------------------------------------------------------
# GS1 PREFIX CLASSIFICATION
#
# The first three digits of a GTIN-13 identify the GS1 Member
# Organisation that issued the company prefix. Most of that is trivia we
# do not need. THREE THINGS IN IT ARE NOT TRIVIA.
# ---------------------------------------------------------------------------

#: NOT GLOBALLY UNIQUE. These ranges are reserved for restricted
#: circulation -- numbers a shop or a company assigns for its OWN
#: internal use, on weighed produce, deli counters, in-store packing.
#:
#:   020-029   restricted circulation within a geographic region
#:   040-049   restricted circulation within a company
#:   200-299   restricted circulation within a geographic region
#:                                      -- GS1 General Specifications
#:
#: THIS IS THE MOST IMPORTANT THING IN THIS FILE AFTER THE CHECK DIGIT,
#: and it is a catalogue-integrity problem rather than a matching one.
#: Two different shops can legitimately assign 2000001 to two completely
#: different things -- loose tomatoes here, chicken pieces there. Both
#: are valid barcodes. Both pass the check digit.
#:
#: Product.gtin carries a UNIQUE constraint, on the stated grounds that
#: "two catalogue rows sharing a barcode means the catalogue is already
#: wrong". Admit one restricted-circulation code and that constraint
#: starts enforcing a falsehood: the SECOND shop's tomatoes get linked
#: to the FIRST shop's chicken, at tier 0, at confidence 1.0.
#:
#: So these never become a catalogue identifier. The row still imports
#: and still matches on its text -- it simply has no barcode.
_RESTRICTED_PREFIX_RANGES = ((20, 29), (40, 49), (200, 299))

#: Not trade items at all: periodicals, books, sheet music, refund
#: receipts and coupons. A coupon is not a product a spaza sells.
_NON_PRODUCT_PREFIX_RANGES = ((977, 977), (978, 979), (980, 980), (981, 983), (990, 999))

#: GS1 South Africa issues 600 and 601, and also serves the wider SADC
#: region. Informational only -- an imported product is perfectly
#: normal, so this is never a reason to reject anything. It is one
#: weak signal among several, useful mainly as "this claims to be a
#: local product and its prefix says otherwise".
_SOUTH_AFRICA_PREFIX_RANGES = ((600, 601),)


def _prefix(value: str) -> Optional[int]:
    """The 3-digit GS1 prefix. GTIN-14 carries a leading packaging
    indicator digit that is NOT part of the prefix, so it is dropped
    first -- reading it would shift every range by one and classify
    almost everything wrongly."""
    if not value or not value.isdigit():
        return None
    body = value[1:] if len(value) == 14 else value
    # GTIN-12 (UPC-A) is a GTIN-13 with an implied leading zero.
    if len(body) == 12:
        body = "0" + body
    return int(body[:3]) if len(body) >= 3 else None


def _in(prefix: Optional[int], ranges) -> bool:
    return prefix is not None and any(low <= prefix <= high for low, high in ranges)


def is_restricted_circulation(value: Optional[str]) -> bool:
    """True for a barcode that is only unique inside one shop or one
    company, and must therefore never identify a catalogue product."""
    return _in(_prefix(value), _RESTRICTED_PREFIX_RANGES)


def is_non_product(value: Optional[str]) -> bool:
    """True for ISSN, ISBN, sheet music, refund receipts and coupons."""
    return _in(_prefix(value), _NON_PRODUCT_PREFIX_RANGES)


def is_south_african_prefix(value: Optional[str]) -> bool:
    """True for 600-601. Informational -- imported stock is normal."""
    return _in(_prefix(value), _SOUTH_AFRICA_PREFIX_RANGES)


def is_catalogue_usable(value: Optional[str]) -> bool:
    """The ONE question the rest of the system should ask: may this
    barcode be used as a shared catalogue identifier?

    Valid check digit, real GTIN length, globally unique, and an actual
    trade item. A caller that asks only is_valid_gtin() gets arithmetic
    without meaning.
    """
    return (
        is_valid_gtin(value)
        and not is_restricted_circulation(value)
        and not is_non_product(value)
    )
