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

from typing import Optional

from src.domains.catalogue.matching.algorithms import normalise
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

    # --- tier 0: barcode ---------------------------------------------------
    if barcode:
        product = CatalogueProductRepository.get_by_gtin(barcode)
        if product:
            return MatchProposal(
                product_id=product.id,
                tier=MatchTier.BARCODE,
                confidence=TIER_CONFIDENCE[MatchTier.BARCODE],
                reason=f"Barcode {barcode} matches this product exactly.",
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
    row_pack = pack if pack is not None and not pack.is_empty else extract_pack_size(name)
    row_brand = BrandRepository.resolve(normalise.brand_slug(brand)) if brand else None

    best: Optional[MatchProposal] = None
    for candidate, similarity in CatalogueProductRepository.search_similar(
        normalised, limit=_CANDIDATE_LIMIT
    ):
        confidence = score_rules_match(
            text_similarity=similarity,
            brand_agrees=_brand_agreement(row_brand, candidate),
            pack_agrees=_pack_agreement(row_pack, candidate),
        )
        if best is None or confidence > best.confidence:
            best = MatchProposal(
                product_id=candidate.id,
                tier=MatchTier.RULES,
                confidence=confidence,
                reason=_explain(similarity, row_brand, row_pack, candidate),
            )

    if best is not None:
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
