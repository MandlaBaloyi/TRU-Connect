"""
Working the review queue: a person deciding what the ladder could not.

THE QUEUE HAS BEEN WRITE-ONLY UNTIL NOW, and its own model says so:
"NOBODY CAN WORK THIS QUEUE YET... rows accumulate unreviewed". That was
the right trade while nothing could review them -- an unreviewed
proposal is simply not applied, and the offer stays unmatched, exactly
how every offer behaved before the catalogue existed.

This is the other half. ReviewStatus.ACCEPTED and REJECTED have existed
since the model was written and nothing has ever set them;
AliasSource.HUMAN likewise. Both were designed for this moment.

WHY A SERVICE AND NOT A SCRIPT. A reviewer's decision has real side
effects -- it attaches a product to an offer and teaches the whole
platform an alias -- and those must happen the same way regardless of
whether the decision arrives from a command line today or the admin
control centre later. V2_09 Part 7 states the rule: management commands
go through the service layer, never raw SQL, because "who approved this,
and when" is exactly the question asked after something goes wrong.

ACCEPTING IS MORE THAN SETTING A STATUS. It writes an alias, and an
alias is GLOBAL -- one person's confirmation answers the same text for
every supplier afterwards. That is the point (the queue gets shorter
over time rather than repeating itself) and it is also why only a human
may do it: AliasSource deliberately excludes RULES, because "tier 3
produces a score, not a certainty, and writing its guesses back as facts
would let one fuzzy match teach the whole platform something wrong".
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.core.base_model import utcnow
from src.core.exceptions import ConflictError, NotFoundError
from src.domains.catalogue.matching.algorithms import normalise
from src.domains.catalogue.matching.models.match_alias import AliasSource
from src.domains.catalogue.matching.models.match_review import MatchReview, ReviewStatus
from src.domains.catalogue.matching.repositories.match_alias_repository import (
    MatchAliasRepository,
)
from src.domains.catalogue.matching.repositories.match_review_repository import (
    MatchReviewRepository,
)
from src.extensions import db

#: Decisions a reviewer may still act on. AUTO_APPLIED is deliberately
#: absent: those were already applied, and a reviewer who disagrees with
#: one is doing something else entirely (unlinking), which needs its own
#: verb rather than being smuggled in as a "review".
_DECIDABLE = (ReviewStatus.PENDING,)


def list_pending(limit: int = 50) -> List[MatchReview]:
    return MatchReviewRepository.list_pending(limit=limit)


def get(review_id: str | UUID) -> MatchReview:
    review = MatchReview.query.filter_by(id=review_id, is_deleted=False).first()
    if review is None:
        raise NotFoundError("Review not found.")
    return review


def counts() -> dict:
    return MatchReviewRepository.count_by_status()


def accept(review_id: str | UUID, *, decided_by_user_id: Optional[str | UUID] = None) -> MatchReview:
    """A person says yes: attach the product, and teach the alias.

    THE ALIAS IS THE POINT. Without it, the next supplier who writes the
    same text queues the same question and a person answers it twice.
    With it, tier 1 resolves it for everyone, free, forever -- which is
    how a review queue shrinks instead of growing.
    """
    review = get(review_id)
    if review.status not in _DECIDABLE:
        raise ConflictError(f"This review is already {review.status.value}.")
    if review.proposed_product_id is None:
        raise ConflictError(
            "There is nothing to accept -- this review proposed no product. "
            "Reject it instead; the offer will stay unmatched."
        )

    # LOADED EXPLICITLY. MatchReview holds supplier_offer_id as a plain
    # column with no relationship attribute -- deliberate, since the FK
    # is ondelete=SET NULL and a review must outlive the offer it was
    # about. So the offer may legitimately be gone, and that is not an
    # error: the DECISION is still worth recording even when the thing
    # it was about has been deleted.
    #
    # Imported locally to keep this module's import graph inside the
    # catalogue domain; the reverse direction is the forbidden one.
    from src.domains.supplier.products.repositories.supplier_offer_repository import (
        SupplierOfferRepository,
    )

    offer = (
        SupplierOfferRepository.get_by_id(review.supplier_offer_id)
        if review.supplier_offer_id
        else None
    )
    if offer is not None:
        offer.product_id = review.proposed_product_id

    # A HUMAN DECISION IS THE STRONGEST ALIAS SOURCE THERE IS. Note that
    # upsert never REPOINTS an existing alias at a different product --
    # if one already exists and disagrees, that contradiction is left
    # for a person to see rather than silently overwritten.
    MatchAliasRepository.upsert(
        matching_key=normalise.matching_key(review.source_text),
        source_text=review.source_text,
        product_id=review.proposed_product_id,
        source=AliasSource.HUMAN,
    )

    review.status = ReviewStatus.ACCEPTED
    review.decided_by_user_id = decided_by_user_id
    review.decided_at = utcnow()
    review.decided_by_source = "HUMAN"
    db.session.commit()
    return review


def reject(
    review_id: str | UUID,
    *,
    decided_by_user_id: Optional[str | UUID] = None,
    reason: Optional[str] = None,
) -> MatchReview:
    """A person says no.

    NO ALIAS IS WRITTEN AND THE OFFER STAYS UNMATCHED -- the model's own
    words: "a rejection is as informative as an acceptance". The offer
    behaves exactly as it did before the catalogue existed, which is a
    safe state rather than a broken one.

    A REJECTION IS NOT A RE-MATCH. Leaving the offer unmatched is
    deliberate: the ladder already proposed its best answer and a person
    disagreed, so proposing again would produce the same one. The next
    real change to the row -- a corrected name or barcode -- is what
    should trigger another attempt, and the match fingerprint already
    makes that happen on its own.
    """
    review = get(review_id)
    if review.status not in _DECIDABLE:
        raise ConflictError(f"This review is already {review.status.value}.")

    review.status = ReviewStatus.REJECTED
    review.decided_by_user_id = decided_by_user_id
    review.decided_at = utcnow()
    review.decided_by_source = "HUMAN"
    if reason:
        # Appended rather than replacing the original reason: why the
        # LADDER proposed it and why a PERSON refused it are both worth
        # keeping, and together they are the useful record.
        review.reason = f"{review.reason} | Rejected: {reason}"[:300]
    db.session.commit()
    return review
