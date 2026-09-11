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
