"""
"Bought by 27 businesses."

THE PROPERTY THAT MAKES THE NUMBER WORTH SHOWING: it counts BUSINESSES,
not units, so one wholesale buyer cannot manufacture a bestseller by
ordering forty cases. That half is enforced in the repository query;
what is tested here is the presentation rule -- when the badge appears,
and exactly what it says.

NO MINIMUM, ON MANDLA'S CALL. I proposed a floor of five on the same
k-anonymity grounds gap_service uses and was overruled, correctly: that
argument depends on a count being paired with a category and an area
and read by suppliers, and none of those apply to a product card. The
reasoning is recorded in social_proof.py's own docstring. These tests
pin the decision so it cannot be quietly reintroduced.
"""
from __future__ import annotations

from src.shared.algorithms import social_proof


class TestTheBadgeAppearsFromOne:
    def test_a_single_buyer_is_shown(self):
        """THE OVERRULED FLOOR. If somebody adds a minimum later, this
        is the test that should make them come and argue for it."""
        assert social_proof.should_show(1) is True
        assert social_proof.label(1) == "Bought by 1 business"

    def test_singular_and_plural_are_both_correct(self):
        assert social_proof.label(1) == "Bought by 1 business"
        assert social_proof.label(2) == "Bought by 2 businesses"

    def test_the_number_increments_exactly(self):
        """NEVER ROUNDED, NEVER "A FEW". A rounded number is a claim
        nobody can check, and soft language is the dark pattern V2_15
        Part 12 bans outright."""
        for n in (1, 2, 3, 7, 26, 99):
            assert str(n) in social_proof.label(n)

    def test_thousands_are_readable(self):
        assert social_proof.label(1500) == "Bought by 1,500 businesses"


class TestNobodyHasBoughtIt:
    def test_zero_shows_no_badge_at_all(self):
        """"Bought by 0 businesses" is true, useless, and reads as a
        warning. The badge is a POSITIVE claim -- its absence says
        nothing, while a zero says something discouraging we did not
        mean."""
        assert social_proof.should_show(0) is False
        assert social_proof.label(0) is None

    def test_unknown_is_treated_as_nothing_to_say(self):
        """A card built before the count was fetched must render, not
        crash."""
        assert social_proof.should_show(None) is False
        assert social_proof.label(None) is None
