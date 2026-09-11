"""
GTIN check-digit tests.

THE FAILURE THESE EXIST TO PREVENT is not "an invalid barcode is
accepted" -- it is "a mistyped barcode matches a DIFFERENT REAL
PRODUCT at tier 0, with confidence 1.0, and nobody reviews it because
tier 0 is the tier nobody questions". See algorithms/gtin.py.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.algorithms import gtin

# Real, well-known GTINs -- their check digits are genuine, which is
# what makes the single-digit tests below meaningful rather than
# circular.
VALID = [
    "6001068668212",   # EAN-13
    "5000112637922",   # EAN-13
    "012000161155",    # UPC-A (12)
    "96385074",        # EAN-8
    "10012000161152",  # GTIN-14 (case)
]


@pytest.mark.parametrize("code", VALID)
def test_real_barcodes_pass(code):
    assert gtin.is_valid_gtin(code), code


@pytest.mark.parametrize("code", VALID)
def test_every_single_digit_typo_is_caught(code):
    """THE WHOLE POINT. A GTIN check digit catches 100% of single-digit
    substitutions, and this asserts it exhaustively rather than
    trusting the claim: every position, every wrong digit."""
    for position in range(len(code)):
        for replacement in "0123456789":
            if replacement == code[position]:
                continue
            typo = code[:position] + replacement + code[position + 1 :]
            assert not gtin.is_valid_gtin(typo), f"{code} -> {typo} slipped through"


@pytest.mark.parametrize("code", VALID)
def test_adjacent_transpositions_are_mostly_caught(code):
    """The standard's one documented blind spot: swapping two adjacent
    digits is caught UNLESS they differ by exactly 5. Asserted rather
    than glossed over, so nobody later believes the scheme is perfect.
    """
    for i in range(len(code) - 1):
        a, b = code[i], code[i + 1]
        if a == b:
            continue
        swapped = code[:i] + b + a + code[i + 2 :]
        if abs(int(a) - int(b)) == 5:
            # Genuinely undetectable by this algorithm.
            assert gtin.is_valid_gtin(swapped)
        else:
            assert not gtin.is_valid_gtin(swapped)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "",
        "   ",
        "abcdefgh",
        "600106866821a",
        "600106866821",     # 12 digits, but an EAN-13 with one dropped
        "60010686682123",   # right length for GTIN-14, wrong checksum
        "123456789",        # 9 digits -- not a GTIN length at all
        "1234567890",       # 10
        "12345678901",      # 11
    ],
)
def test_malformed_and_wrong_length_are_rejected(bad):
    assert not gtin.is_valid_gtin(bad)


def test_lengths_that_are_not_gtins_are_rejected_even_if_checksum_would_pass():
    """9, 10 and 11 digits are not GTINs of any kind. The old import
    rule accepted 8-to-14 inclusive, so these were admitted and then
    failed to match anything, forever."""
    for length in (9, 10, 11):
        body = "1" * (length - 1)
        candidate = body + str(gtin.check_digit(body))
        assert not gtin.is_valid_gtin(candidate)


def test_normalise_returns_none_rather_than_a_bad_barcode():
    """The failure mode of a caller forgetting to check must be a
    MISSED match, never a wrong one."""
    assert gtin.normalise_gtin("6001068668212") == "6001068668212"
    assert gtin.normalise_gtin("6001068668213") is None
    assert gtin.normalise_gtin(None) is None


# ---------------------------------------------------------------------
# GS1 PREFIX CLASSIFICATION
# ---------------------------------------------------------------------

def test_restricted_circulation_codes_are_not_catalogue_usable():
    """THE CATALOGUE-INTEGRITY CASE, and it is not a matching bug.

    Prefixes 020-029, 040-049 and 200-299 are restricted circulation:
    numbers a shop assigns for its OWN use on weighed produce and deli
    goods. They have valid check digits and they are NOT globally
    unique -- two shops can each label something 2000001.

    Product.gtin is UNIQUE. Admit one of these and the second shop's
    completely different product silently links to the first shop's,
    at tier 0, at confidence 1.0.
    """
    for body in ("200000100000", "020000100000", "045000100000"):
        code = body + str(gtin.check_digit(body))
        assert gtin.is_valid_gtin(code), f"{code} should be arithmetically sound"
        assert gtin.is_restricted_circulation(code), code
        assert not gtin.is_catalogue_usable(code), f"{code} must never identify a product"


def test_books_and_coupons_are_not_trade_items():
    """978/979 are ISBNs, 977 is ISSN, 981-983 and 990-999 are coupons,
    980 is a refund receipt. None of them is a thing a spaza sells."""
    assert gtin.is_valid_gtin("9780306406157")
    assert gtin.is_non_product("9780306406157")
    assert not gtin.is_catalogue_usable("9780306406157")


def test_real_products_remain_usable():
    """The classification must not cost the ordinary case anything."""
    for code in ("6001108028044", "5449000054227"):
        assert gtin.is_catalogue_usable(code), code
        assert not gtin.is_restricted_circulation(code)
        assert not gtin.is_non_product(code)


def test_south_african_prefixes_are_recognised():
    """600-601 is GS1 South Africa. Informational only -- imported
    stock is completely normal, so this never rejects anything."""
    assert gtin.is_south_african_prefix("6001108028044")      # Savanna, SA
    assert not gtin.is_south_african_prefix("5449000054227")  # Coke, BE
    # And being foreign is not a reason to refuse it.
    assert gtin.is_catalogue_usable("5449000054227")


def test_gtin_14_prefix_skips_the_packaging_indicator():
    """A GTIN-14 prepends a packaging indicator digit that is NOT part
    of the GS1 prefix. Reading it would shift every range by one and
    misclassify almost everything."""
    body = "1" + "600110802804"          # indicator 1 + an SA GTIN-13 body
    code = body + str(gtin.check_digit(body))
    assert gtin.is_valid_gtin(code)
    assert gtin.is_south_african_prefix(code), "600 must still be seen through the indicator"


def test_upc_a_is_treated_as_a_13_digit_code_with_a_leading_zero():
    """GTIN-12 is a GTIN-13 whose leading zero is implied. Without that,
    a US UPC would read as prefix '012' rather than '001'."""
    assert gtin.is_valid_gtin("012000161155")
    assert gtin.is_catalogue_usable("012000161155")
    assert not gtin.is_restricted_circulation("012000161155")
