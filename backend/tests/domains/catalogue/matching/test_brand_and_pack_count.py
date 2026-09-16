"""
The last two facts the matcher was reading and then throwing away.

FOUR BUGS OF ONE FAMILY were found by running the real matcher over a
real catalogue. Three were pack SIZE and are pinned in test_pack_size
and test_normalise_keys. These are the other two, plus the thing that
only became visible once they were fixed.

  1. THE PACK COUNT WAS EXTRACTED AND DISCARDED. catalogue.products had
     no pack_quantity column, so a single 36g bag of Doritos at R6.00
     and a case of 24 at R139.50 agreed on every fact the catalogue
     stored -- same brand, same 36g consumer unit -- and merged.

  2. THE BRAND WAS NEVER READ AT ALL. `brand` is not a column on
     supplier_offers, and nothing derived it from the name, so
     _brand_agreement always saw None and the -0.30 penalty never
     fired. 47 of 72 distinct review decisions were competitors
     proposed as one another: Fanta against Coca-Cola, Surf against
     Omo, aQuelle against Bonaqua.

  3. AND THEN AMBIGUITY BETWEEN TWO WRONG ANSWERS. With the penalty
     finally applied, the wrong candidates all scored LOW and therefore
     CLOSE -- 0.19, 0.17, 0.24 -- and a 0.05 ambiguity margin called
     that a tie. Thirteen pairs went to a human at confidences as low
     as 19%, asking which of two products that are plainly not it was
     more nearly it.

MEASURED ON 1,049 REAL OFFERS: the review queue went from 216 rows /
72 decisions to 51 rows / 18 decisions, with zero brand collisions and
zero products mixing sizes or counts.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.algorithms.brand_detect import (
    detect_brand,
    resolve_brand,
)
from src.domains.catalogue.matching.algorithms.confidence import (
    MatchDecision,
    MatchProposal,
    MatchTier,
)
from src.domains.catalogue.matching.algorithms.pack_size import extract_pack_size


class TestTheBrandIsReadFromTheName:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("Fanta Orange Cooldrink 500ml", "Fanta"),
            ("Coca-Cola 500ml", "Coca-Cola"),
            # WORD ORDER DOES NOT MATTER, because the matching key it
            # feeds treats order as meaningless. A brand reader that
            # insisted on position would disagree with its own tier.
            ("2LT COCA COLA", "Coca-Cola"),
            # THROUGH THE ABBREVIATION EXPANDER: "W/STAR" is not in the
            # brand list, "White Star" is, and normalise_text bridges
            # them before this ever looks.
            ("W/STAR Maize Meal", "White Star"),
        ],
    )
    def test_it_finds_a_declared_brand(self, name, expected):
        assert detect_brand(name) == expected

    @pytest.mark.parametrize(
        "name",
        [
            # THE FIRST-WORD HEURISTIC WOULD HAVE TAKEN ALL OF THESE.
            # 41 products in the seeded catalogue lead with "Generic".
            "Generic Rice 2kg",
            "Washing Powder 2kg",
            "Potatoes 10kg",
            "White Bread Loaf",
            "Maize Meal 10kg",
        ],
    )
    def test_a_generic_leading_word_is_not_a_brand(self, name):
        assert detect_brand(name) is None

    def test_longest_match_wins(self):
        """"White Star" must beat a bare "White", or every loaf of white
        bread joins the maize meal."""
        assert detect_brand("White Star Maize Meal 5kg") == "White Star"
        assert detect_brand("White Bread Loaf") is None

    def test_it_matches_whole_words_not_substrings(self):
        """"Ace" is a brand; "Acetone" is not one wearing a disguise."""
        assert detect_brand("Ace Maize Meal 2.5kg") == "Ace"
        assert detect_brand("Acetone Remover 100ml") is None

    def test_a_stated_brand_outranks_a_detected_one(self):
        """A brand that arrived with an import is something a supplier
        SAID. One read out of a name is something we inferred."""
        assert resolve_brand("Koo", "Fanta Orange 500ml") == "Koo"
        assert resolve_brand(None, "Fanta Orange 500ml") == "Fanta"
        assert resolve_brand("   ", "Fanta Orange 500ml") == "Fanta"


class TestThePackCountIsRead:
    @pytest.mark.parametrize(
        "name,count",
        [
            ("Doritos Chips 36g x24", 24),
            ("COKE 2LT PET 6PK", 6),
            ("12x500ml", 12),
            # NAMED COUNTS, added after "Five Roses Tea 26 bags" was
            # proposed against the same tea in 100s at 79% -- same
            # brand, no measure on either side, so nothing could object.
            ("Five Roses Tea 26 bags", 26),
            ("Twinsaver Toilet Paper 9s", 9),
        ],
    )
    def test_it_finds_the_count(self, name, count):
        assert extract_pack_size(name).pack_quantity == count

    @pytest.mark.parametrize("name", ["Maize Meal 10kg", "Ace Maize Meal 2.5kg", "Coke 2L"])
    def test_a_MEASURE_is_not_a_count(self, name):
        """THE RISK THE NAMED-COUNT PATTERN INTRODUCES. A bare
        "(\\d+)\\s*\\w+" would read "Maize Meal 10kg" as ten of
        something the moment the measure parser missed -- and a WRONG
        count is worse than none, because it fabricates a disagreement
        and suppresses a correct match. The noun list is closed."""
        assert extract_pack_size(name).pack_quantity is None

    def test_a_single_and_a_case_are_different_sizes(self):
        """THE DORITOS CASE. Identical consumer unit, identical brand,
        nearly identical text -- the count is the only thing telling
        R6.00 from R139.50."""
        single = extract_pack_size("Doritos Chips 36g")
        case = extract_pack_size("Doritos Chips 36g x24")

        assert single.to_base() == case.to_base(), "the consumer unit really is the same"
        assert single.pack_quantity != case.pack_quantity, "and the count is what differs"


class TestAmbiguityBetweenTwoWrongAnswers:
    """A near-tie only means something when the candidates are
    plausible. review_threshold's own docstring already said so: "below
    it there is no plausible candidate at all, so a new catalogue
    product is created rather than a reviewer being handed a question
    with no good answer."
    """

    def _proposal(self, confidence: float, **kwargs) -> MatchProposal:
        return MatchProposal(
            product_id=None,
            tier=MatchTier.RULES,
            confidence=confidence,
            reason="",
            **kwargs,
        )

    def test_a_tie_between_implausible_candidates_creates_a_new_product(self):
        """THE REGRESSION. Two wrong answers scoring 0.19 and 0.17 are
        not a difficult decision, they are an absent one."""
        assert self._proposal(0.19, ambiguous=True).decision is MatchDecision.CREATE_NEW

    def test_a_tie_between_plausible_candidates_still_goes_to_a_human(self):
        """This is what the ambiguity flag is FOR -- auto-linking a
        contested match is how "Coca-Cola 2L" ends up attached to
        Coca-Cola Zero."""
        assert self._proposal(0.95, ambiguous=True).decision is MatchDecision.REVIEW

    def test_a_contradicted_barcode_always_goes_to_a_human(self):
        """Tier 0's confidence is a constant 1.0, so there is no score
        here to fall below a threshold -- the contradiction is the only
        thing arguing against it."""
        assert self._proposal(1.0, contradicted=True).decision is MatchDecision.REVIEW
