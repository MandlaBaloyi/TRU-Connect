"""
MatchReview -- the middle band of the confidence gate, made durable.

A proposal confident enough to be plausible but not confident enough to
act on lands here and waits for a person. That is the entire mechanism
protecting the catalogue from its own cleverness: the alternative is
guessing, and a wrong match tells a business "R89 here, R74 there" about
two different products.

NOBODY CAN WORK THIS QUEUE YET, and that is worth stating rather than
discovering. The admin control centre is deferred until the ecosystem is
further along, so rows accumulate unreviewed. The consequence is
deliberately harmless: an unreviewed proposal is simply not applied, and
the offer stays unmatched -- which is exactly how every offer behaves
today. Nothing regresses; some things merely do not improve yet.

WRITE-ONLY IS THE POINT FOR NOW. The queue records what the platform
would have done and why, so when a reviewer does arrive there is a real
backlog with real reasoning attached rather than a cold start.

EVERY AUTO-LINK IS RECORDED HERE TOO, already resolved. Not just the
ones needing a decision -- the confident ones as well, marked
AUTO_APPLIED. That is what makes an auto-link reversible and
explainable: a supplier disputing a match can be shown which tier
proposed it, at what confidence, and on what text.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.core.base_model import BaseModel
from src.extensions import db


class ReviewStatus(str, enum.Enum):
    """Name == value, per this codebase's enum convention."""

    #: Waiting for a person. The offer stays unmatched meanwhile.
    PENDING = "PENDING"
    #: Confidence cleared the auto-link bar; already applied. Recorded
    #: anyway so it can be explained and undone.
    AUTO_APPLIED = "AUTO_APPLIED"
    #: A person agreed. The link is applied and an alias is written.
    ACCEPTED = "ACCEPTED"
    #: A person disagreed. The offer stays unmatched and no alias is
    #: written -- a rejection is as informative as an acceptance.
    REJECTED = "REJECTED"


class MatchReview(BaseModel):
    __tablename__ = "match_reviews"
    __table_args__ = (
        db.Index("ix_match_reviews_status", "status"),
        db.Index("ix_match_reviews_supplier_offer_id", "supplier_offer_id"),
        {"schema": "catalogue"},
    )

    #: The offer being matched. SET NULL rather than cascade: an offer
    #: being deleted must not erase the record of a decision made about
    #: it, for the same reason import_rows keeps its history.
    supplier_offer_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("supplier.supplier_offers.id", ondelete="SET NULL"),
        nullable=True,
    )

    #: What the supplier actually wrote, snapshotted. A reviewer needs
    #: the original words, and the offer's own name could change before
    #: anyone gets to this row.
    source_text = db.Column(db.String(300), nullable=False)

    #: What was proposed. NULL means "nothing plausible was found" --
    #: a real outcome, not a missing value.
    proposed_product_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("catalogue.products.id", ondelete="SET NULL"),
        nullable=True,
    )

    #: Which rung proposed it -- MatchTier. Stored as a plain string
    #: rather than a database enum on purpose: tiers will be added as
    #: the ladder grows, and a new rung should not need a migration to
    #: an enum type before it can be recorded.
    tier = db.Column(db.String(20), nullable=False)

    #: 0.000 to 1.000. Numeric, never float -- the same money-column
    #: discipline this codebase applies elsewhere, for the same reason:
    #: a threshold comparison must not depend on binary rounding.
    confidence = db.Column(db.Numeric(4, 3), nullable=False)

    #: Why, in words a supplier could be shown. Never a debug string.
    reason = db.Column(db.String(300), nullable=False)

    status = db.Column(
        db.Enum(ReviewStatus, name="match_review_status", schema="catalogue"),
        nullable=False,
        default=ReviewStatus.PENDING,
    )

    #: Who decided, for ACCEPTED and REJECTED. NULL for PENDING and for
    #: AUTO_APPLIED, where nobody did.
    decided_by_user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=True
    )
    decided_at = db.Column(db.DateTime(timezone=True), nullable=True)

    #: EVERY SIGNAL THAT PRODUCED THE CONFIDENCE, not just the number.
    #:
    #: `confidence` answers "how sure". This answers "on what grounds",
    #: and they are different questions. 0.94 from a barcode and 0.94
    #: from a lucky trigram score look identical in one column and are
    #: not remotely the same claim.
    #:
    #: THREE THINGS THIS PAYS FOR:
    #:
    #:   DEBUGGING. "Why is this supplier's juice linked to Coca-Cola"
    #:   gets a real answer instead of a shrug.
    #:
    #:   DISPUTES. A supplier challenging a match is owed the reasoning
    #:   -- already promised in V2_00: "so a disputed match can be
    #:   explained". A sentence is a courtesy; the numbers behind it are
    #:   the evidence.
    #:
    #:   THE TRAINING SET. Every reviewed row is a labelled example on a
    #:   genuinely hard case -- hard by construction, because the easy
    #:   ones never reached a human. Recording the features AT DECISION
    #:   TIME is the difference between having a dataset in a year and
    #:   wishing the columns had been there. They cannot be recovered
    #:   afterwards: the catalogue will have changed.
    #:
    #: JSONB RATHER THAN A COLUMN PER SIGNAL, deliberately. The signal
    #: set is not stable -- category agreement, image attributes and an
    #: external GTIN lookup are all planned (V2_11) and none exist yet.
    #: A column each would mean a migration per signal and a table full
    #: of nulls for the ones a given tier cannot produce. A tier records
    #: what it actually observed and nothing else.
    #:
    #: NULL INSIDE MEANS "NO SIGNAL", never "disagreed" -- the same
    #: distinction _brand_agreement draws, for the same reason. A
    #: product with no brand is not a product whose brand was wrong.
    evidence = db.Column(JSONB, nullable=False, default=dict, server_default="{}")

    #: WHO OR WHAT DECIDED. A stable column rather than a key in
    #: `evidence`, because an audit must be able to separate "a person
    #: said so" from "a model said so" without parsing JSON -- and
    #: because the day a model's judgements are used as training labels,
    #: distinguishing them from human ones is the difference between a
    #: dataset and a rumour.
    #:
    #: SYSTEM  the deterministic ladder (tiers 0-3). The default today.
    #: HUMAN   a reviewer.
    #: MODEL   the paid tier, when it exists. Never built yet.
    decided_by_source = db.Column(
        db.String(10), nullable=False, default="SYSTEM", server_default="SYSTEM"
    )
