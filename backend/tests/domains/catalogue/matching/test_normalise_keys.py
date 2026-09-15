"""
The tier-2 exact-match key, and the two ways it used to be ambiguous.

WHY THIS TIER DESERVES ITS OWN TESTS. Tier 2 returns confidence 1.0
with the words "matches this product word for word", and consults NO
pack size -- the -0.40 mismatch penalty lives in tier 3 and never runs.
So a collision here is not a slightly-wrong match, it is a maximally
confident wrong match with a reason a human would read and believe.

BOTH BUGS BELOW WERE FOUND BY RUNNING THE MATCHER OVER A REAL
CATALOGUE, not by reading it. That is worth recording: every unit test
in this domain passed throughout, because they all supplied their own
normalised text or their own PackSize, and these are failures of what
the code DERIVES rather than of what it does with it.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.algorithms import normalise


class TestTheDecimalPointSurvives:
    """THE BUG, measured on the seeded catalogue:

        "Ace Maize Meal 2.5kg" -> "ace maize meal 2 5kg"
                               -> "25kgacemaizemeal"
        "Ace Maize Meal 25kg"  -> "25kgacemaizemeal"

    One canonical product holding a 2.5kg bag at R40.50 and a 25kg bag
    at R340.50, presented to shopkeepers as alternatives, at confidence
    1.0.
    """

    def test_two_point_five_kg_is_not_twenty_five_kg(self):
        assert normalise.matching_key("Ace Maize Meal 2.5kg") != normalise.matching_key(
            "Ace Maize Meal 25kg"
        )

    def test_all_three_maize_sizes_are_three_keys(self):
        keys = {
            normalise.matching_key(f"Ace Maize Meal {size}")
            for size in ("2.5kg", "5kg", "25kg")
        }

        assert len(keys) == 3

    def test_a_comma_decimal_and_a_full_stop_decimal_are_one_size(self):
        """South African files use both, for the same bag."""
        assert normalise.matching_key("Rama 1,5kg") == normalise.matching_key("Rama 1.5kg")

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Product.", "product"),
            ("Mrs. Balls Chutney", "mrs balls chutney"),
            ("...Odd.", "odd"),
        ],
    )
    def test_a_full_stop_that_is_not_a_decimal_is_still_stripped(self, text, expected):
        assert normalise.normalise_text(text) == expected


class TestTheKeyIsNotAmbiguousByConstruction:
    """Joining sorted tokens with NOTHING lets any two adjacent tokens
    concatenate into whatever a single token could have spelled. The
    decimal fix above stops the pair that was actually found; the
    separator stops the class."""

    def test_two_words_do_not_collide_with_one(self):
        assert normalise.matching_key("Bread Roll") != normalise.matching_key("Breadroll")

    def test_a_split_number_does_not_collide_with_a_joined_one(self):
        assert normalise.matching_key("Sugar 2 5kg") != normalise.matching_key("Sugar 25kg")


class TestWhatMustNotHaveChanged:
    """The properties tier 2 exists for. If the fixes above broke any of
    these, they cost more than they bought."""

    def test_word_order_still_does_not_matter(self):
        """The whole point: one supplier lists brand-first, another
        size-first, and both land on the same product."""
        assert normalise.matching_key("Coca-Cola 2LT") == normalise.matching_key(
            "2LT COCA COLA"
        )

    def test_punctuation_is_still_broadly_stripped(self):
        assert normalise.normalise_text("W/STAR Maize 5kg") == "white star maize 5kg"
        assert normalise.normalise_text("S&V Chips 125g") == "salt vinegar chips 125g"

    def test_abbreviations_still_expand(self):
        """Expansion happens after punctuation is stripped, which is
        what turns "W/STAR" into a phrase this can recognise."""
        assert "white star" in normalise.normalise_text("W/STAR Maize Meal")

    def test_accents_are_still_folded(self):
        assert normalise.normalise_text("Café Latte") == "cafe latte"

    def test_nothing_in_is_nothing_out(self):
        assert normalise.matching_key(None) == ""
        assert normalise.matching_key("") == ""
        assert normalise.matching_key("   ") == ""
