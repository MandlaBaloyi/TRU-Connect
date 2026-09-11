"""
Working the review queue.

Until now the queue was WRITE-ONLY -- the model says so itself: "NOBODY
CAN WORK THIS QUEUE YET... rows accumulate unreviewed". ACCEPTED,
REJECTED and AliasSource.HUMAN were all designed for this moment and
nothing had ever set them.

THE ACCEPT PATH HAS REAL SIDE EFFECTS and they are the point: it links
the offer AND teaches a global alias, so the next supplier who writes
the same words is matched for free. That is how a review queue shrinks
instead of repeating itself.
"""
from __future__ import annotations

import pytest

from src.core.exceptions import ConflictError, NotFoundError
from src.domains.catalogue.matching.algorithms import normalise
from src.domains.catalogue.matching.models.match_alias import AliasSource
from src.domains.catalogue.matching.models.match_review import ReviewStatus
from src.domains.catalogue.matching.repositories.match_alias_repository import (
    MatchAliasRepository,
)
from src.domains.catalogue.matching.repositories.match_review_repository import (
    MatchReviewRepository,
)
from src.domains.catalogue.matching.services import matching_service, review_service
from src.domains.catalogue.products.models.product import Product
from src.domains.catalogue.products.models.taxonomy import ProductCategory, ProductUnit
from src.domains.supplier.products.services import product_service
from src.extensions import db

SOURCE_TEXT = "COKE 2LT PET BOTTLE RETURNABLE"


@pytest.fixture()
def product(db_session):
    row = Product(
        name="Coca-Cola Original 2L",
        normalized_name=normalise.normalise_text("Coca-Cola Original 2L"),
        category=ProductCategory.BEVERAGES,
    )
    db.session.add(row)
    db.session.flush()
    return row


@pytest.fixture()
def offer(make_supplier, make_supplier_profile):
    profile = make_supplier_profile(make_supplier())
    return product_service.create_product(
        supplier_profile_id=profile.id,
        name="Some Unrelated Thing",
        category=ProductCategory.BEVERAGES,
        price_cents=2200,
        selling_unit=ProductUnit.EACH,
    )


@pytest.fixture()
def pending(product, offer):
    review = MatchReviewRepository.record(
        supplier_offer_id=offer.id,
        source_text=SOURCE_TEXT,
        proposed_product_id=product.id,
        tier="RULES",
        confidence=0.82,
        reason="Description is 82% similar.",
        status=ReviewStatus.PENDING,
        evidence={"text_similarity": 0.82, "brand_agrees": None},
    )
    db.session.commit()
    return review


def test_accepting_links_the_offer(pending, offer, product):
    review_service.accept(pending.id)

    assert offer.product_id == product.id
    assert pending.status is ReviewStatus.ACCEPTED
    assert pending.decided_at is not None
    assert pending.decided_by_source == "HUMAN"


def test_accepting_teaches_a_global_alias(pending, product):
    """THE REASON ACCEPTING MATTERS MORE THAN ONE ROW. Without the alias
    the next supplier writing the same words queues the same question and
    a person answers it twice."""
    review_service.accept(pending.id)

    alias = MatchAliasRepository.get(normalise.matching_key(SOURCE_TEXT))
    assert alias is not None
    assert alias.product_id == product.id
    assert alias.source is AliasSource.HUMAN


def test_the_alias_answers_the_next_supplier_for_free(pending, product):
    """Proved through the real ladder rather than by inspecting a row:
    after one person decides, tier 1 resolves it for everyone."""
    review_service.accept(pending.id)
    db.session.commit()

    proposal = matching_service.propose_match(name=SOURCE_TEXT)

    assert proposal.product_id == product.id
    assert proposal.tier.value == "ALIAS"


def test_rejecting_does_not_attach_the_proposed_product(pending, offer, product):
    """"A rejection is as informative as an acceptance" -- but it must
    not write an alias, or one refusal would teach the platform a
    falsehood.

    NOTE WHAT IS ASSERTED: that the offer is not attached to the
    REJECTED product, not that it has no product at all. Since
    create_product started matching, a freshly created offer already
    carries whatever the ladder gave it -- here, its own new catalogue
    entry. "Unmatched" was the right assertion before that change and is
    the wrong one now."""
    before = offer.product_id

    review_service.reject(pending.id, reason="Actually Fanta Orange")

    assert offer.product_id != product.id, "the refused product was not attached"
    assert offer.product_id == before, "and nothing else moved either"
    assert pending.status is ReviewStatus.REJECTED
    assert MatchAliasRepository.get(normalise.matching_key(SOURCE_TEXT)) is None
    assert "Actually Fanta Orange" in pending.reason
    assert "82% similar" in pending.reason, "the ladder's own reason is kept too"


def test_a_decision_cannot_be_made_twice(pending):
    review_service.accept(pending.id)
    with pytest.raises(ConflictError):
        review_service.accept(pending.id)
    with pytest.raises(ConflictError):
        review_service.reject(pending.id)


def test_accepting_a_proposal_with_no_product_is_refused(offer):
    """CREATE_NEW rows propose nothing. There is nothing to link, and
    silently doing nothing would look like success."""
    review = MatchReviewRepository.record(
        supplier_offer_id=offer.id,
        source_text="Something Brand New",
        proposed_product_id=None,
        tier="RULES",
        confidence=0.10,
        reason="No existing product matched.",
        status=ReviewStatus.PENDING,
    )
    db.session.commit()

    with pytest.raises(ConflictError):
        review_service.accept(review.id)


def test_a_missing_review_is_not_found(db_session):
    import uuid

    with pytest.raises(NotFoundError):
        review_service.get(uuid.uuid4())


def test_accepting_is_written_to_the_audit_trail(app, db_session, pending, make_user):
    """ACCEPTING IS NOT A ONE-ROW CHANGE.

    It writes a GLOBAL alias: from then on any supplier who types those
    same words is matched automatically, forever. The blast radius is
    every supplier on the platform, which is the threshold at which an
    act belongs in the audit trail alongside every other privileged
    thing a staff member can do.

    match_reviews already records decided_by_user_id, and that is the
    OPERATIONAL record -- what happened to this proposal. This is the
    SECURITY record, in the one table where "what did this staff member
    do" is a single query rather than a tour of per-domain tables
    somebody has to know exist.
    """
    from src.domains.auth.models.user import UserRole, VerificationStatus

    staff = make_user(
        "staff-audit@truconnect.co.za",
        role=UserRole.ADMIN,
        verification_status=VerificationStatus.VERIFIED,
    )
    db.session.commit()

    review_service.accept(pending.id, decided_by_user_id=str(staff.id))

    row = db.session.execute(
        db.text(
            "SELECT user_id, actor_type, metadata FROM security.audit_events "
            "WHERE event_name = 'catalogue.match_accepted' ORDER BY timestamp DESC LIMIT 1"
        )
    ).fetchone()

    assert row is not None, "accepting a match left no audit trail"
    assert str(row[0]) == str(staff.id)
    assert row[1] == "admin"
    assert row[2]["source_text"] == SOURCE_TEXT


def test_rejecting_is_written_to_the_audit_trail(app, db_session, pending, make_user):
    """A refusal is a decision too, and the reason is the useful part."""
    from src.domains.auth.models.user import UserRole, VerificationStatus

    staff = make_user(
        "staff-audit2@truconnect.co.za",
        role=UserRole.ADMIN,
        verification_status=VerificationStatus.VERIFIED,
    )
    db.session.commit()

    review_service.reject(
        pending.id, decided_by_user_id=str(staff.id), reason="Actually Fanta Orange 2L"
    )

    row = db.session.execute(
        db.text(
            "SELECT user_id, metadata FROM security.audit_events "
            "WHERE event_name = 'catalogue.match_rejected' ORDER BY timestamp DESC LIMIT 1"
        )
    ).fetchone()

    assert row is not None, "rejecting a match left no audit trail"
    assert row[1]["reason"] == "Actually Fanta Orange 2L"
