"""
May a paid call be made right now?

THE CEILING IS CHECKED BEFORE THE CALL, NOT AFTER, which is the only
placement that actually bounds anything -- checking afterwards tells you
what you already spent.

EXCEEDING THE BUDGET IS NOT AN ERROR CONDITION. It means fall back to
the free tiers. Running out of money must degrade completeness, never
correctness, and must never fail a supplier's import: an unmatched offer
is exactly how every offer behaves today, so the worst outcome of a
spent budget is a catalogue that fills in more slowly.

That is why this returns a decision rather than raising. Callers are
expected to carry on.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.ai.config import ai_config
from src.shared.ai.decisions.repositories import AIDecisionRepository


@dataclass(frozen=True)
class SpendDecision:
    allowed: bool
    reason: str
    budget_cents: int
    spent_cents: int

    @property
    def remaining_cents(self) -> int:
        return max(0, self.budget_cents - self.spent_cents)


def may_spend(estimated_cost_cents: int = 0) -> SpendDecision:
    """Whether a paid call is permitted, given what is already spent.

    THE ESTIMATE IS INCLUDED IN THE COMPARISON on purpose. Checking only
    what has already been spent lets the very call that breaches the
    ceiling through -- fine for one cheap call, not fine for a batch of
    several thousand.
    """
    budget = ai_config.monthly_budget_cents()

    if budget <= 0:
        return SpendDecision(
            allowed=False,
            reason="No AI budget is configured (AI_MONTHLY_BUDGET_CENTS is 0).",
            budget_cents=0,
            spent_cents=0,
        )

    spent = AIDecisionRepository.spend_this_month_cents()
    if spent + max(0, estimated_cost_cents) > budget:
        return SpendDecision(
            allowed=False,
            reason=f"Monthly AI budget reached ({spent} of {budget} cents spent).",
            budget_cents=budget,
            spent_cents=spent,
        )

    return SpendDecision(
        allowed=True,
        reason="Within budget.",
        budget_cents=budget,
        spent_cents=spent,
    )
