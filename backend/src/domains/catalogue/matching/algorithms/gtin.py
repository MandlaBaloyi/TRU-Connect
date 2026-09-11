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
