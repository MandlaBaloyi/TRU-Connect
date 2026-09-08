"""
The free half of the matching ladder: normalisation and pack-size rules.

NO DATABASE, NO NETWORK, NO MODEL. Every case here is a string a real
supplier might type, and every one it handles is a row that never needs
to reach the paid tier. This file is where the matching bill gets
reduced, so it is worth being generous with cases.
"""
from __future__ import annotations

import pytest

from src.domains.catalogue.matching.algorithms.normalise import (
    brand_slug,
    matching_key,
    normalise_text,
    strip_accents,
)
from src.domains.catalogue.matching.algorithms.pack_size import PackSize, extract_pack_size


# --- normalise -------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        # 2lt collapses to 2l -- see the measure normalisation tests
        # below. Suppliers write the same size three ways and trigram
        # similarity treats them as three different strings.
        ("Coca-Cola 2LT", "coca cola 2l"),
        ("COCA COLA", "coca cola"),
        ("  Coca   Cola  ", "coca cola"),
        ("Sunlight (Dishwashing) 750ml", "sunlight dishwashing 750ml"),
        ("Bread & Rolls", "bread rolls"),
        ("Omo 2kg**SPECIAL**", "omo 2kg special"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalise_text(raw, expected):
    assert normalise_text(raw) == expected


def test_accents_are_stripped_because_an_encoding_is_not_a_fact_about_the_product():
    assert strip_accents("café") == "cafe"
    assert normalise_text("Café Crème") == "cafe creme"


@pytest.mark.parametrize(
    "a,b",
    [
        ("Coca-Cola 2LT", "2LT COCA COLA"),
        ("Bread White 700g", "700g white bread"),
        ("Omo Washing Powder 2kg", "2KG OMO washing powder"),
    ],
)
def test_word_order_stops_mattering(a, b):
    """Suppliers list brand-first, size-first, or whatever their own
    system exported. A matcher that treats those as different products
    fails the easy cases before it reaches a hard one."""
    assert matching_key(a) == matching_key(b)


def test_matching_key_still_separates_genuinely_different_products():
    assert matching_key("Coca-Cola 2L") != matching_key("Coca-Cola 1L")
    assert matching_key("Coke 2L") != matching_key("Fanta 2L")


def test_brand_slug_collapses_spellings():
    assert brand_slug("Coca-Cola") == "cocacola"
    assert brand_slug("Coca Cola") == "cocacola"
    assert brand_slug("COCA-COLA") == "cocacola"


# --- pack size -------------------------------------------------------------


@pytest.mark.parametrize(
    "text,quantity,measure",
    [
        ("Coke 2LT", 2, "L"),
        ("Coke 2L", 2, "L"),
        ("Coke 2 Litre", 2, "L"),
        ("Coke 2 litres", 2, "L"),
        ("Sunlight 750ml", 750, "ML"),
        ("Sunlight 750 ML", 750, "ML"),
        ("Omo 2KG", 2, "KG"),
        ("Bread 700g", 700, "G"),
        ("Sugar 1 kilogram", 1, "KG"),
    ],
)
def test_the_consumer_size_is_read(text, quantity, measure):
    result = extract_pack_size(text)
    assert result.unit_quantity == quantity
    assert result.unit_measure == measure


@pytest.mark.parametrize(
    "text,pack",
    [
        ("Coke 2L 6PK", 6),
        ("Coke 2L 6 pack", 6),
        ("Coke 2L x6", 6),
        ("Coke 2L x 6", 6),
        ("Coke 2L case of 6", 6),
        ("Coke 2L box of 12", 12),
        ("Coke 2L 6's", 6),
        ("Coke 2L pk6", 6),
    ],
)
def test_the_pack_count_is_read(text, pack):
    assert extract_pack_size(text).pack_quantity == pack


def test_the_size_digits_are_not_mistaken_for_the_pack_count():
    """"12x500ml" is twelve bottles of 500ml. Without hiding the measure
    before searching for a pack count, the 500 is visible to the pack
    patterns and whichever matched first would win."""
    result = extract_pack_size("Coke 12x500ml")
    assert result.unit_quantity == 500
    assert result.unit_measure == "ML"
    assert result.pack_quantity == 12


def test_two_litres_and_two_thousand_millilitres_are_the_same_product():
    """The reason to_base exists. These compare equal or the catalogue
    ends up with two rows for one drink."""
    assert extract_pack_size("Coke 2L").to_base() == extract_pack_size("Coke 2000ml").to_base()
    assert extract_pack_size("Omo 2kg").to_base() == extract_pack_size("Omo 2000g").to_base()


def test_base_measure_reports_what_the_number_is_counted_in():
    assert extract_pack_size("Coke 2L").base_measure == "ML"
    assert extract_pack_size("Omo 2kg").base_measure == "G"
    assert extract_pack_size("Bread White").base_measure is None


@pytest.mark.parametrize("text", ["Bread White", "Building Sand", "Loose Potatoes", "", None])
def test_products_with_no_size_return_empty_rather_than_a_guess(text):
    """Plenty of real products have no measure at all. Empty leaves the
    row for a later tier; a guess silently corrupts a per-unit price."""
    assert extract_pack_size(text).is_empty


def test_a_fractional_size_is_refused_rather_than_rounded():
    """unit_quantity is an integer column. 1.5kg becoming 1 or 2 would
    put a wrong per-unit price on a product card, and wrong is worse
    than absent."""
    result = extract_pack_size("Sugar 1.5kg")
    assert result.unit_quantity is None
    assert result.unit_measure is None


def test_a_pack_of_one_is_not_a_pack():
    assert extract_pack_size("Coke 2L x1").pack_quantity is None


def test_a_word_that_merely_ends_in_a_measure_letter_is_not_a_size():
    """"Melrose 250" has no unit; "Special" ends in an l. Neither is a
    2-litre anything, and a matcher that thinks so invents sizes."""
    assert extract_pack_size("Melrose Cheese Special").is_empty


def test_pack_size_equality_is_by_value():
    assert extract_pack_size("Coke 2L 6pk") == PackSize(
        unit_quantity=2, unit_measure="L", pack_quantity=6
    )


# --- the confidence gate ---------------------------------------------------


def test_the_gate_bands(monkeypatch):
    from src.domains.catalogue.matching.algorithms.confidence import MatchDecision, decide

    monkeypatch.delenv("MATCHING_AUTO_LINK_CONFIDENCE", raising=False)
    monkeypatch.delenv("MATCHING_REVIEW_CONFIDENCE", raising=False)

    assert decide(1.0) is MatchDecision.AUTO_LINK
    assert decide(0.92) is MatchDecision.AUTO_LINK
    assert decide(0.91) is MatchDecision.REVIEW
    assert decide(0.70) is MatchDecision.REVIEW
    assert decide(0.69) is MatchDecision.CREATE_NEW
    assert decide(0.0) is MatchDecision.CREATE_NEW


def test_the_thresholds_come_from_the_environment(monkeypatch):
    """What counts as "sure enough" is a business risk decision that
    should move as the catalogue proves itself, without a deploy."""
    from src.domains.catalogue.matching.algorithms.confidence import MatchDecision, decide

    monkeypatch.setenv("MATCHING_AUTO_LINK_CONFIDENCE", "0.99")
    assert decide(0.95) is MatchDecision.REVIEW


def test_a_malformed_threshold_falls_back_rather_than_crashing(monkeypatch):
    """A typo in an env var must never be why the backend will not boot."""
    from src.domains.catalogue.matching.config import matching_config

    monkeypatch.setenv("MATCHING_AUTO_LINK_CONFIDENCE", "not-a-number")
    assert matching_config.auto_link_threshold() == 0.92


def test_the_paid_tier_is_off_unless_deliberately_turned_on(monkeypatch):
    from src.domains.catalogue.matching.config import matching_config

    monkeypatch.delenv("MATCHING_MODE", raising=False)
    assert matching_config.use_ai_tier() is False
    monkeypatch.setenv("MATCHING_MODE", "deterministic")
    assert matching_config.use_ai_tier() is False
    monkeypatch.setenv("MATCHING_MODE", "full")
    assert matching_config.use_ai_tier() is True


def test_a_pack_size_disagreement_sinks_an_otherwise_similar_match():
    """THE MOST DANGEROUS CASE IN THIS DOMAIN. "Coke 2L" and "Coke
    500ml" read as nearly the same text and are absolutely not the same
    product -- linking them puts a per-unit price on a card that is out
    by a factor of four."""
    from src.domains.catalogue.matching.algorithms.confidence import (
        MatchDecision,
        decide,
        score_rules_match,
    )

    looks_alike = score_rules_match(text_similarity=0.93, brand_agrees=True, pack_agrees=False)
    assert decide(looks_alike) is not MatchDecision.AUTO_LINK


def test_an_unknown_brand_or_pack_is_not_treated_as_a_disagreement():
    """"Building Sand" has no brand and no pack. That is an absence of
    evidence, not evidence against."""
    from src.domains.catalogue.matching.algorithms.confidence import score_rules_match

    unknown = score_rules_match(text_similarity=0.90, brand_agrees=None, pack_agrees=None)
    disagrees = score_rules_match(text_similarity=0.90, brand_agrees=False, pack_agrees=False)

    assert unknown == pytest.approx(0.90)
    assert disagrees < unknown


def test_agreement_helps_but_cannot_manufacture_certainty():
    from src.domains.catalogue.matching.algorithms.confidence import score_rules_match

    # approx, not ==: 0.60 + 0.05 + 0.05 is 0.7000000000000001 in
    # binary floating point. The clamp at 1.0 is the real assertion
    # here -- bonuses must never manufacture certainty past it.
    assert score_rules_match(text_similarity=0.60, brand_agrees=True, pack_agrees=True) == pytest.approx(0.70)
    assert score_rules_match(text_similarity=1.0, brand_agrees=True, pack_agrees=True) == 1.0


# --- abbreviation expansion ------------------------------------------------
#
# EVERY CASE HERE CAME OUT OF A MEASUREMENT, not imagination. A
# two-supplier trial resolved 40% of matchable rows; reading the misses
# showed none were ambiguous, they were shorthand. Adding these took the
# same file to 80%, for free and permanently.


@pytest.mark.parametrize(
    "written,expanded",
    [
        ("W/STAR SUPER MAIZE 10KG", "white star super maize 10kg"),
        ("SIMBA S&V CHIPS 125G", "simba salt vinegar chips 125g"),
        ("5 ROSES TEA 100S", "five roses tea 100s"),
        ("SUNLIGHT DISHWASH LIQ 750ML", "sunlight dishwashing liquid 750ml"),
        ("KOO BAKED BEANS TOM SAUCE 410G", "koo baked beans tomato sauce 410g"),
        ("OMO WASHING PWDR 2KG", "omo washing powder 2kg"),
    ],
)
def test_supplier_shorthand_is_expanded(written, expanded):
    assert normalise_text(written) == expanded


def test_punctuation_is_stripped_before_expansion():
    """"W/STAR" and "S&V" are meaningless as single tokens and
    unambiguous as phrases -- which only works because the slash and
    ampersand are already spaces by the time expansion runs."""
    assert "white star" in normalise_text("W/STAR MAIZE")
    assert "salt vinegar" in normalise_text("S&V CHIPS")


def test_words_that_are_not_shorthand_are_left_alone():
    """This never invents, only replaces what it recognises."""
    assert normalise_text("Castle Lager Draught") == "castle lager draught"


@pytest.mark.parametrize(
    "a,b",
    [
        ("Sprite 2 Litre", "Sprite 2L"),
        ("Sunfoil Oil 2LT", "Sunfoil Oil 2l"),
        ("Clover Milk 1LT", "Clover Milk 1L"),
        ("Omo 2 KG", "Omo 2kg"),
        ("Sunlight 750 ML", "Sunlight 750ml"),
    ],
)
def test_the_same_size_written_differently_normalises_the_same(a, b):
    """SPRITE 2 LITRE failed to match a catalogue "Sprite 2L" until
    measures were canonicalised. Three spellings, one string."""
    assert normalise_text(a) == normalise_text(b)


def test_a_measure_is_not_invented_where_there_is_none():
    assert normalise_text("Melrose Cheese Special") == "melrose cheese special"


# --- containment and ambiguity ---------------------------------------------


def test_a_subset_of_the_catalogue_name_scores_higher():
    """MEASURED: every remaining miss after abbreviations had this shape
    -- "COLGATE TOOTHPASTE" against "Colgate Regular Toothpaste". The
    supplier simply wrote less, and trigram similarity PENALISES the
    extra words in the catalogue name."""
    from src.domains.catalogue.matching.algorithms.confidence import score_rules_match

    without = score_rules_match(text_similarity=0.80, brand_agrees=None, pack_agrees=None)
    with_containment = score_rules_match(
        text_similarity=0.80, brand_agrees=None, pack_agrees=None, row_words_all_present=True
    )
    assert with_containment > without


def test_containment_is_worth_less_than_a_pack_disagreement_costs():
    """Containment is suggestive; a pack mismatch is decisive. A subset
    match with the WRONG SIZE must never out-score its own penalty."""
    from src.domains.catalogue.matching.algorithms.confidence import (
        MatchDecision,
        decide,
        score_rules_match,
    )

    subset_wrong_size = score_rules_match(
        text_similarity=0.95,
        brand_agrees=True,
        pack_agrees=False,
        row_words_all_present=True,
    )
    assert decide(subset_wrong_size) is not MatchDecision.AUTO_LINK


def test_two_close_candidates_are_a_question_not_a_match():
    """"Coca-Cola 2L" is equally a subset of "Coca-Cola Original 2L" and
    "Coca-Cola Zero 2L". Picking whichever sorted first would be a coin
    toss presented as a fact."""
    from src.domains.catalogue.matching.algorithms.confidence import (
        MatchDecision,
        MatchProposal,
        MatchTier,
    )

    contested = MatchProposal(
        product_id=None, tier=MatchTier.RULES, confidence=0.98, reason="x", ambiguous=True
    )
    assert contested.decision is MatchDecision.REVIEW


def test_a_clear_winner_is_still_auto_linked():
    from src.domains.catalogue.matching.algorithms.confidence import (
        MatchDecision,
        MatchProposal,
        MatchTier,
    )

    clear = MatchProposal(product_id=None, tier=MatchTier.RULES, confidence=0.98, reason="x")
    assert clear.decision is MatchDecision.AUTO_LINK
