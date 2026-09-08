"""
The confidence gate: what to DO with a proposed match.

THIS IS THE MOST IMPORTANT FILE IN THE MATCHING DOMAIN, and the shortest.
Everything else finds candidates; this decides whether anyone is allowed
to act on one without a human looking.

WHY THE GATE IS ON CONFIDENCE AND NOT ON TIER OR MODEL. Two useful
properties fall out of that choice:

  A CHEAPER MODEL CANNOT PRODUCE WRONG MATCHES. Swap Opus for Sonnet and
  the answers get less certain, not less correct -- so more rows land in
  the review band and fewer get auto-linked. The bill drops,
  completeness drops, accuracy does not. That is what makes the model a
  tunable dial rather than a risk.

  A NEW TIER NEEDS NO NEW RULES. Whatever tier 5 turns out to be, it
  reports a confidence and this file already knows what to do with it.

WHY A WRONG MATCH IS WORSE THAN NO MATCH. No match means one supplier's
offer sits alone and cannot be compared -- exactly how every offer
behaves today, so nothing is lost. A wrong match means the catalogue
claims two different things are the same product and shows a business a
price comparison that is a lie. One is an absence; the other is
misinformation with TRU Connect's name on it.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.domains.catalogue.matching.config import matching_config


class MatchTier(str, enum.Enum):
    """Which rung of the ladder produced a proposal. Recorded rather
    than inferred, so a disputed match can be explained: "your barcode
    matched exactly" is a different conversation from "the description
    was 88% similar".

    Name == value, the convention every enum in this codebase follows,
    since SQLAlchemy persists a member's NAME rather than its .value.
    """

    BARCODE = "BARCODE"           # tier 0 -- exact GTIN. Free, certain.
    ALIAS = "ALIAS"               # tier 1 -- this exact text confirmed before. Free.
    NORMALISED = "NORMALISED"     # tier 2 -- same words, any order. Free.
    RULES = "RULES"               # tier 3 -- brand + pack + trigram. Free.
    AI = "AI"                     # tier 4 -- costs money.


class MatchDecision(str, enum.Enum):
    """What the platform is permitted to do with a proposal."""

    AUTO_LINK = "AUTO_LINK"
    REVIEW = "REVIEW"
    CREATE_NEW = "CREATE_NEW"

    #: NOTHING WAS ATTEMPTED -- matching is switched off. Never returned
    #: by decide(); only by the linking service, which checks the kill
    #: switch before proposing anything.
    #:
    #: THIS EXISTS BECAUSE OF A REAL BUG A TEST CAUGHT. Disabled matching
    #: used to surface as a confidence of 0.0, which is exactly what
    #: "no plausible candidate" looks like -- so the gate read it as
    #: CREATE_NEW and the kill switch quietly filled the catalogue with a
    #: new product for every imported row. "Off" and "found nothing" must
    #: not share a representation.
    SKIPPED = "SKIPPED"


#: Inherent confidence of the free tiers, before any per-candidate
#: scoring. Tier 3 does NOT appear here -- its confidence is computed
#: per candidate from how well the text and pack size actually agreed,
#: which is the whole reason it is the last free tier rather than
#: another lookup.
TIER_CONFIDENCE = {
    # A GTIN is the one identifier that means exactly one product. Not
    # 1.0 as a superstition about certainty -- it IS certain; a barcode
    # collision means the catalogue is already wrong, and the unique
    # constraint on Product.gtin is what prevents that.
    MatchTier.BARCODE: 1.0,
    # A confirmed alias is a decision a human or a high-confidence match
    # already made about this exact text. Just short of a barcode,
    # because the text could in principle have been reused by a
    # different supplier for a different product.
    MatchTier.ALIAS: 0.99,
    # Same words, any order, nothing else in common required. Strong,
    # but "Coke 2L" could legitimately be two products if one is a
    # returnable bottle and the other is not.
    MatchTier.NORMALISED: 0.95,
}


@dataclass(frozen=True)
class MatchProposal:
    """One candidate, and how sure we are.

    product_id is None only for CREATE_NEW, where the point is that
    nothing plausible was found.
    """

    product_id: Optional[UUID]
    tier: MatchTier
    confidence: float
    #: Why, in words a supplier could be shown. Never a debug string.
    reason: str

    @property
    def decision(self) -> MatchDecision:
        return decide(self.confidence)


def decide(confidence: float) -> MatchDecision:
    """The gate. Thresholds come from the environment (see
    matching_config) because what counts as "sure enough" is a business
    risk decision that should move as the catalogue proves itself."""
    if confidence >= matching_config.auto_link_threshold():
        return MatchDecision.AUTO_LINK
    if confidence >= matching_config.review_threshold():
        return MatchDecision.REVIEW
    return MatchDecision.CREATE_NEW


def score_rules_match(
    *,
    text_similarity: float,
    brand_agrees: Optional[bool],
    pack_agrees: Optional[bool],
) -> float:
    """Tier 3's confidence, from how much actually agreed.

    TEXT SIMILARITY IS THE BASE and the other two adjust it, rather than
    all three being averaged. Similarity is the only signal always
    available; brand and pack are frequently unknown on one side or the
    other, and an unknown must not be scored as a disagreement --
    "Building Sand" has no brand and no pack, and that is not evidence
    against anything.

    A DISAGREEMENT IS HEAVILY PENALISED, deliberately asymmetric to the
    bonus for agreement. Two products whose descriptions read alike but
    whose PACK SIZES differ are the single most dangerous case in this
    entire domain: "Coke 2L" and "Coke 500ml" are 90% similar as text
    and are absolutely not the same product. Getting that wrong puts a
    per-unit price on a card that is off by a factor of four.
    """
    score = max(0.0, min(1.0, text_similarity))

    if brand_agrees is True:
        score += 0.05
    elif brand_agrees is False:
        score -= 0.30

    if pack_agrees is True:
        score += 0.05
    elif pack_agrees is False:
        score -= 0.40

    return max(0.0, min(1.0, score))
