"""
The matching ladder: given what a supplier wrote, which catalogue
product is it?

    tier 0  BARCODE     exact GTIN                       free, certain
    tier 1  ALIAS       this exact text, confirmed before free
    tier 2  NORMALISED  same words, any order            free
    tier 3  RULES       brand + pack + trigram           free
    tier 4  AI          extraction and adjudication      COSTS MONEY

EACH RUNG THAT HITS MEANS THE NEXT NEVER RUNS. That ordering is the
entire cost strategy: the cheap, certain, explainable answers are tried
first, and the paid tier only ever sees what genuinely could not be
resolved for free. Tier 4 does not exist yet -- when it does, it is one
more branch at the bottom of this function and nothing above it changes.

THIS FUNCTION DECIDES NOTHING. It proposes. Whether a proposal is
applied, queued for a person, or turned into a new catalogue product is
the confidence gate's call (algorithms/confidence.py), and separating
the two is what keeps "how confident are we" from being tangled up with
"what are we allowed to do about it".

WHY IT IS SAFE TO RUN WITH THE AI SWITCHED OFF FOREVER. Every tier here
is deterministic and free. Rows the free tiers cannot resolve become
unmatched offers -- exactly how every offer behaves today -- so the
worst case of never turning tier 4 on is a catalogue that fills in more
slowly, never one that fills in wrongly.
"""
from __future__ import annotations

from typing import List, Optional

from src.domains.catalogue.matching.algorithms import gtin, normalise
from src.domains.catalogue.matching.algorithms.confidence import (
    TIER_CONFIDENCE,
    MatchProposal,
    MatchTier,
    score_rules_match,
)
from src.domains.catalogue.matching.algorithms.pack_size import PackSize, extract_pack_size
from src.domains.catalogue.matching.config import matching_config
from src.domains.catalogue.matching.repositories.match_alias_repository import (
    MatchAliasRepository,
)
from src.domains.catalogue.products.models.product import Product
from src.domains.catalogue.products.repositories.brand_repository import BrandRepository
from src.domains.catalogue.products.repositories.product_repository import (
    CatalogueProductRepository,
)

#: How many trigram candidates tier 3 weighs. Small on purpose: beyond
#: the closest handful, similarity has already fallen far enough that a
#: candidate is not plausible, and scoring more only makes a wrong one
#: more likely to sneak past on a lucky brand agreement.
_CANDIDATE_LIMIT = 5

#: How far apart the top two candidates must score before the better one
#: can be acted on alone. Below this they are indistinguishable, and the
#: honest answer is a person -- see the ambiguity check in propose_match.
_AMBIGUITY_MARGIN = 0.05


def propose_match(
    *,
    name: str,
    barcode: Optional[str] = None,
    brand: Optional[str] = None,
    pack: Optional[PackSize] = None,
) -> MatchProposal:
    """Which catalogue product this row most likely is, and how sure.

    `pack` may be passed in when the supplier gave real pack columns --
    those are better evidence than anything parsed out of a description,
    so they are trusted over the text when present.
    """
    if not matching_config.is_matching_enabled():
        return MatchProposal(
            product_id=None,
            tier=MatchTier.RULES,
            confidence=0.0,
            reason="Matching is switched off.",
        )

    # The row's own evidence, resolved ONCE. Tier 0's consistency check
    # and tier 3's scoring both need the same two facts.
    row_pack = pack if pack is not None and not pack.is_empty else extract_pack_size(name)
    row_brand = BrandRepository.resolve(normalise.brand_slug(brand)) if brand else None

    # --- tier 0: barcode ---------------------------------------------------
    #
    # THREE GATES, NOT ONE, because this tier returns confidence 1.0 and
    # the words "matches this product exactly". Everything here exists to
    # make sure that sentence is true when it is said.
    #
    #   1. is_catalogue_usable -- sound check digit, a real GTIN length,
    #      AND globally unique. A restricted-circulation code (an
    #      in-store number for weighed produce, prefix 020-029 / 040-049
    #      / 200-299) has a perfect check digit and is unique only
    #      inside one shop; looking one up matches another shop's
    #      unrelated product.
    #
    #   2. the lookup itself.
    #
    #   3. _barcode_contradiction -- the row's own brand and pack size
    #      must not ARGUE AGAINST the product the barcode named. A valid
    #      barcode on the wrong product is the one error the first two
    #      gates cannot see.
    #
    # Import validates too, but this is the second of the two doors into
    # matching (the API is the other) and a rule enforced at only one
    # entrance is not enforced.
    if gtin.is_catalogue_usable(barcode):
        product = CatalogueProductRepository.get_by_gtin(barcode)
        if product:
            contradiction = _barcode_contradiction(row_brand, row_pack, product)
            return MatchProposal(
                product_id=product.id,
                tier=MatchTier.BARCODE,
                confidence=TIER_CONFIDENCE[MatchTier.BARCODE],
                reason=(
                    contradiction
                    or f"Barcode {barcode} matches this product exactly."
                ),
                contradicted=contradiction is not None,
            )

    normalised = normalise.normalise_text(name)
    key = normalise.matching_key(name)

    # --- tier 1: a confirmed alias ----------------------------------------
    if key:
        alias = MatchAliasRepository.get(key)
        if alias:
            MatchAliasRepository.record_hit(alias)
            return MatchProposal(
                product_id=alias.product_id,
                tier=MatchTier.ALIAS,
                confidence=TIER_CONFIDENCE[MatchTier.ALIAS],
                reason="This exact description has been matched to this product before.",
            )

    # --- tier 2: same words, any order ------------------------------------
    if key:
        product = CatalogueProductRepository.get_by_matching_key(key)
        if product:
            return MatchProposal(
                product_id=product.id,
                tier=MatchTier.NORMALISED,
                confidence=TIER_CONFIDENCE[MatchTier.NORMALISED],
                reason="The description matches this product word for word.",
            )

    # --- tier 3: brand, pack and fuzzy text -------------------------------
    # row_pack and row_brand were resolved above, before tier 0, because
    # the barcode consistency check needs the same two facts.
    row_words = set(normalised.split(" ")) if normalised else set()

    scored: List[MatchProposal] = []
    for candidate, similarity in CatalogueProductRepository.search_similar(
        normalised, limit=_CANDIDATE_LIMIT
    ):
        candidate_words = set((candidate.normalized_name or "").split(" "))
        confidence = score_rules_match(
            text_similarity=similarity,
            brand_agrees=_brand_agreement(row_brand, candidate),
            pack_agrees=_pack_agreement(row_pack, candidate),
            row_words_all_present=bool(row_words) and row_words <= candidate_words,
        )
        scored.append(
            MatchProposal(
                product_id=candidate.id,
                tier=MatchTier.RULES,
                confidence=confidence,
                reason=_explain(similarity, row_brand, row_pack, candidate),
            )
        )

    if scored:
        scored.sort(key=lambda proposal: proposal.confidence, reverse=True)
        best = scored[0]

        # TWO CANDIDATES TOO CLOSE TO SEPARATE is not a strong match, it
        # is a question. "Coca-Cola 2L" is equally a subset of
        # "Coca-Cola Original 2L" and "Coca-Cola Zero 2L", and picking
        # whichever sorted first would be a coin toss presented as a
        # fact. Flagged rather than scored down, so a reviewer sees a
        # real confidence next to a real reason.
        if len(scored) > 1 and (best.confidence - scored[1].confidence) < _AMBIGUITY_MARGIN:
            return MatchProposal(
                product_id=best.product_id,
                tier=best.tier,
                confidence=best.confidence,
                reason=best.reason + " Another product scored almost as closely.",
                ambiguous=True,
            )

        return best

    # --- nothing plausible -------------------------------------------------
    # Confidence 0, so the gate returns CREATE_NEW. Stated as a proposal
    # rather than None so every caller handles one shape.
    return MatchProposal(
        product_id=None,
        tier=MatchTier.RULES,
        confidence=0.0,
        reason="No catalogue product resembles this description.",
    )


def _barcode_contradiction(row_brand, row_pack: PackSize, candidate: Product) -> Optional[str]:
    """Does the row's own evidence ARGUE AGAINST the barcode's answer?

    Returns the reason when it does, None when it does not.

    WHY THIS EXISTS. A GTIN names exactly one trade item, so tier 0
    returns confidence 1.0 and the words "matches this product exactly"
    -- and that is precisely what makes a WRONG barcode dangerous. It is
    not a near miss. A supplier who types a cooldrink's barcode onto a
    juice, or slips one digit onto another live code, gets a confident
    link to a different real product that no one reviews, because tier 0
    is the tier nobody questions.

    ONLY THE STRUCTURED SIGNALS ARE USED, AND THAT WAS MEASURED RATHER
    THAN ASSUMED. Text similarity was the obvious candidate and it does
    not work here. Measured on real rewordings against real mismatches:

        COKE 2LT PET          -> Coca-Cola Original 2L   0.312  CORRECT
        Clover Fresh Milk 2L  -> Coca-Cola Original 2L   0.439  WRONG

    The wrong pair scores HIGHER than the right one, because supplier
    shorthand ("COKE") is further from the catalogue name than an
    unrelated product that happens to share a size and some letters.
    Across ten legitimate rewordings and seven mismatches the ranges
    overlapped with no threshold separating them. Any text gate here
    would reject real matches to catch fake ones.

    Brand and pack DISAGREEMENT are different: both are structured, both
    are compared in normalised form, and both are already trusted enough
    elsewhere that a pack disagreement costs -0.40 in tier 3.

    NONE IS NOT DISAGREEMENT, the same rule the rest of this module
    follows. A row with no brand column and no parseable pack size
    contradicts nothing -- it simply has nothing to say, and a barcode
    with nothing against it is still the best identifier there is.

    WHAT THIS DOES NOT CATCH, said plainly so nobody assumes otherwise:
    a wrong barcode on a product of the SAME pack size with no brand
    column given. "Liqui Fruit Orange 2L" carrying Coke 2L's barcode has
    no structured contradiction available. That case needs an external
    GTIN lookup -- an independent source saying what the barcode really
    is -- which is the next piece of work, not this one.
    """
    if _brand_agreement(row_brand, candidate) is False:
        return (
            "The barcode matches this product, but the brand does not. "
            "Please check the barcode is on the right product."
        )
    if _pack_agreement(row_pack, candidate) is False:
        return (
            "The barcode matches this product, but the pack size does not. "
            "Please check the barcode is on the right product."
        )
    return None


def _brand_agreement(row_brand, candidate: Product) -> Optional[bool]:
    """True, False, or None for "cannot tell".

    NONE IS NOT FALSE, and the distinction matters. Plenty of real
    products have no brand at all -- loose potatoes, building sand -- and
    scoring an absence as a disagreement would push honest matches below
    the gate.
    """
    if row_brand is None or candidate.brand_id is None:
        return None
    return row_brand.id == candidate.brand_id


def _pack_agreement(row_pack: PackSize, candidate: Product) -> Optional[bool]:
    """Whether the sizes are the same product, compared in base units.

    2L and 2000ml agree. 2L and 500ml do not, and that disagreement is
    the most valuable signal in the whole tier: those two descriptions
    read almost identically as text, and linking them would put a
    per-unit price on a card that is out by a factor of four.
    """
    row_base = row_pack.to_base() if row_pack else None
    candidate_base = PackSize(
        unit_quantity=candidate.unit_quantity,
        unit_measure=candidate.unit_measure.value if candidate.unit_measure else None,
    ).to_base()

    if row_base is None or candidate_base is None:
        return None
    return row_base == candidate_base


def _explain(similarity: float, row_brand, row_pack: PackSize, candidate: Product) -> str:
    """Words a supplier could be shown, not a debug string. Someone
    disputing a match is owed a reason, and "0.87" is not one."""
    parts = [f"Description is {round(similarity * 100)}% similar"]
    if row_brand is not None and candidate.brand_id == row_brand.id:
        parts.append("same brand")
    if _pack_agreement(row_pack, candidate) is True:
        parts.append("same pack size")
    elif _pack_agreement(row_pack, candidate) is False:
        parts.append("DIFFERENT pack size")
    return ", ".join(parts) + "."
