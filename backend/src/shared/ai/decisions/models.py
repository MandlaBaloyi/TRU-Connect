"""
AIDecision -- every model call this platform has ever made, and what it
cost.

TWO JOBS, AND THE SECOND ONE IS WHY THIS IS A TABLE RATHER THAN A LOG
LINE.

  IT ENFORCES THE BUDGET. A ceiling that nothing measures is decoration.
  Spend-to-date is summed from these rows before every paid call, so
  AI_MONTHLY_BUDGET_CENTS is a real limit rather than an intention.

  IT MAKES DECISIONS ANSWERABLE. When a supplier disputes a match, or a
  business disputes a verification, someone has to be able to say what
  was asked, what came back, how sure it was, and which model said so.
  A log file rotates away; this does not.

DELIBERATELY IN shared/, NOT IN A DOMAIN. Matching needs it today,
verification will need it next, and column mapping after that. A ledger
per feature would mean three budgets that each believe they are the only
one spending -- which is three ways to blow through one ceiling.

Same reasoning as shared/audit, and the same shape.

WHAT IS NOT STORED: the full prompt and the full response. They are
large, they are reproducible from the input reference, and a supplier's
catalogue text sitting in a second table forever is a liability rather
than an asset. A hash of the input is enough to answer "was this the
same question" without keeping the question.
"""
from __future__ import annotations

import enum

from src.core.base_model import BaseModel
from src.extensions import db


class AIDecisionKind(str, enum.Enum):
    """Name == value, per this codebase's enum convention."""

    EXTRACT = "EXTRACT"
    ADJUDICATE = "ADJUDICATE"


class AIDecision(BaseModel):
    __tablename__ = "ai_decisions"
    __table_args__ = (
        # The budget query is "everything since the start of this month",
        # so created_at leads. Without it, the spend check gets slower
        # with every call ever made -- and it runs before every call.
        db.Index("ix_ai_decisions_created_at", "created_at"),
        db.Index("ix_ai_decisions_feature", "feature"),
        {"schema": "platform"},
    )

    #: Which part of the platform asked: "catalogue_matching",
    #: "verification". A plain string rather than an enum on purpose --
    #: a new feature should not need a migration before it can spend.
    feature = db.Column(db.String(50), nullable=False)

    kind = db.Column(
        db.Enum(AIDecisionKind, name="ai_decision_kind", schema="platform"), nullable=False
    )

    #: The provider that answered: "claude", "fake", "dry-run(claude)".
    #: Recorded so a bad run traces to the thing that made it, and so
    #: fake and dry-run rows are obviously distinguishable from real
    #: spend when reading the table.
    provider = db.Column(db.String(40), nullable=False)
    model = db.Column(db.String(60), nullable=False)

    #: SHA-256 of the input. Answers "was this the same question" without
    #: storing the question.
    input_hash = db.Column(db.String(64), nullable=False)

    input_tokens = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    output_tokens = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))
    cached_input_tokens = db.Column(
        db.Integer, nullable=False, default=0, server_default=db.text("0")
    )

    #: Cents, integer, never a float -- the same money convention the
    #: rest of this codebase uses, for the same reason: a ceiling
    #: comparison must not depend on binary rounding.
    cost_cents = db.Column(db.Integer, nullable=False, default=0, server_default=db.text("0"))

    #: The confidence returned, for ADJUDICATE. Null for EXTRACT, which
    #: does not judge anything.
    confidence = db.Column(db.Numeric(4, 3), nullable=True)

    #: Set when the call failed. A failed call still COSTS in wall-clock
    #: and sometimes in tokens, and a run that failed repeatedly is
    #: exactly what someone reading this table needs to see.
    error = db.Column(db.String(300), nullable=True)
