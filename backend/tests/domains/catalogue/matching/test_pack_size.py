"""
Reading a pack size out of a supplier's own words.

THE REGRESSION THIS FILE EXISTS FOR, found by running the real matcher
over a real catalogue rather than by reading the code:

    "Ace Maize Meal 2.5kg" parsed to NO PACK SIZE AT ALL, because 2.5 is
    not an integer and unit_quantity is an integer column. The first
    supplier to list it therefore created a CATALOGUE ENTRY WITH NO PACK
    SIZE -- from a name that visibly contains one.

    That entry then behaved as a magnet. _pack_agreement returns None
    ("unknown") when either side has no base size, and unknown is
    correctly not scored as disagreement -- so the -0.40 penalty that
    exists for exactly this case never fired. "Ace Maize Meal 5kg"
    scored 1.0 against it instead of 0.65 and auto-linked. So did the
    25kg.

    Measured on the seeded catalogue: ONE canonical product holding
    2.5kg, 5kg and 25kg maize meal from ten suppliers, priced R40.50 to
    R340.50, offered to shopkeepers as alternatives to each other.

The fix expresses a fractional size in the base unit the module already
reduces everything to for comparison -- 2.5kg is exactly 2500g -- so
nothing is rounded and nothing is guessed.

WHY THESE ARE UNIT TESTS ON A PURE FUNCTION. This is the cheapest layer
at which the bug is visible, and the ladder tests above it all pass an
explicit PackSize, which is precisely why they never caught it: they
test what the matcher does with a size, not whether it found one.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.algorithms.pack_size import extract_pack_size


class TestFractionalSizesSurvive:
    """THE BUG. Each of these used to parse to nothing at all."""

    @pytest.mark.parametrize(
        "text,base",
        [
            ("Ace Maize Meal 2.5kg", 2500),
            ("Coke 1.5L", 1500),
            ("Rama 1,5kg", 1500),  # comma decimal, as South African files write it
            ("Sunlight Liquid 0.75L", 750),
        ],
    )
    def test_a_fractional_size_is_kept_in_the_base_unit(self, text, base):
        assert extract_pack_size(text).to_base() == base

    def test_the_three_maize_meals_no_longer_agree(self):
        """THE EXACT SHAPE OF THE PRODUCTION BUG. If these three ever
        compare equal again, one canonical product is holding a
        ten-fold price range and calling it a choice."""
        sizes = {
            extract_pack_size(f"Ace Maize Meal {written}").to_base()
            for written in ("2.5kg", "5kg", "25kg")
        }

        assert sizes == {2500, 5000, 25000}
        assert len(sizes) == 3, "three different products must have three different sizes"

    def test_a_fraction_and_its_whole_equivalent_still_compare_equal(self):
        """The conversion must not break the property to_base() exists
        for: the same real size written two ways is one size."""
        assert extract_pack_size("Rama 1.5kg").to_base() == extract_pack_size("Rama 1500g").to_base()
        assert extract_pack_size("Coke 2L").to_base() == extract_pack_size("Coke 2000ml").to_base()


class TestItStillRefusesToGuess:
    """The rule the module opened with, and the fix must not weaken it:
    an unparsed size leaves the row for a later tier; a WRONG one
    silently corrupts a per-unit price."""

    def test_a_fraction_of_the_smallest_unit_is_refused(self):
        """There is nowhere below millilitres to go, so 2.5ml stays
        unparsed rather than becoming 2 or 3."""
        assert extract_pack_size("Additive 2.5ml").to_base() is None

    def test_something_finer_than_the_base_unit_is_refused(self):
        assert extract_pack_size("Essence 0.0005L").to_base() is None

    def test_a_product_with_no_size_has_no_size(self):
        """"Bread White" and "Building Sand" are real products with no
        measure at all, and that is not a failure."""
        assert extract_pack_size("Bread White").is_empty
        assert extract_pack_size("Building Sand").is_empty

    def test_nothing_at_all_is_empty(self):
        assert extract_pack_size(None).is_empty
        assert extract_pack_size("").is_empty


class TestThePackCountIsUnaffected:
    """The size and the count are different facts, and the fix touched
    only the first. These pin that the second still works -- including
    the case the measure-blanking exists for."""

    def test_a_six_pack_of_two_litres(self):
        pack = extract_pack_size("COKE 2LT PET 6PK")

        assert pack.to_base() == 2000
        assert pack.pack_quantity == 6

    def test_twelve_by_five_hundred(self):
        """The measure's digits are hidden before the pack search, or
        the 500 and the 12 compete and whichever matches first wins."""
        pack = extract_pack_size("12x500ml")

        assert pack.to_base() == 500
        assert pack.pack_quantity == 12

    def test_a_pack_of_one_is_not_a_pack(self):
        assert extract_pack_size("Soap 100g 1pk").pack_quantity is None
