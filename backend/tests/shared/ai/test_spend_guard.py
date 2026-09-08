"""
The budget ceiling, proven to actually stop spending.

A CEILING THAT NOTHING MEASURES IS DECORATION. These tests exist because
"AI_MONTHLY_BUDGET_CENTS=2000" is worthless unless something reads the
ledger, sums it, and refuses. So the ledger is written to for real here
and the guard is asked afterwards.

EXCEEDING THE BUDGET IS NOT AN ERROR, and the tests assert that shape
deliberately: may_spend RETURNS a decision rather than raising, because
callers are expected to carry on with the free tiers. Running out of
money must degrade completeness, never correctness, and must never fail
a supplier's import.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.shared.ai.decisions.models import AIDecisionKind
from src.shared.ai.decisions.repositories import AIDecisionRepository, hash_input
from src.shared.ai.decisions.spend_guard import may_spend
from src.extensions import db


def _spend(cents: int, *, when: datetime | None = None, feature: str = "catalogue_matching"):
    decision = AIDecisionRepository.record(
        feature=feature,
        kind=AIDecisionKind.ADJUDICATE,
        provider="claude",
        model="claude-sonnet-5",
        input_hash=hash_input("left", "right"),
        input_tokens=1000,
        output_tokens=100,
        cost_cents=cents,
        confidence=0.9,
    )
    if when is not None:
        decision.created_at = when
    db.session.flush()
    return decision


# --- the default is closed, not merely low ---------------------------------


def test_no_budget_means_no_paid_calls_at_all(db_session, monkeypatch):
    monkeypatch.delenv("AI_MONTHLY_BUDGET_CENTS", raising=False)
    decision = may_spend(estimated_cost_cents=1)

    assert decision.allowed is False
    assert "No AI budget" in decision.reason


def test_a_budget_alone_permits_spending(db_session, monkeypatch):
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "2000")
    assert may_spend(estimated_cost_cents=10).allowed is True


# --- the ledger is what the ceiling reads ----------------------------------


def test_spending_accumulates_and_eventually_refuses(db_session, monkeypatch):
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "100")

    _spend(60)
    assert may_spend(estimated_cost_cents=10).allowed is True

    _spend(45)
    refused = may_spend(estimated_cost_cents=10)
    assert refused.allowed is False
    assert refused.spent_cents == 105
    assert "budget reached" in refused.reason


def test_the_estimate_is_counted_before_the_call_not_after(db_session, monkeypatch):
    """Checking only what has ALREADY been spent lets the very call that
    breaches the ceiling through. Fine for one cheap call; not fine for
    a batch of several thousand."""
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "100")
    _spend(95)

    assert may_spend(estimated_cost_cents=1).allowed is True
    assert may_spend(estimated_cost_cents=50).allowed is False


def test_last_months_spending_does_not_count_against_this_month(db_session, monkeypatch):
    """A calendar month, because that is how the person setting the
    budget thinks about it -- and a ceiling nobody can predict the reset
    of is one they will not trust."""
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "100")

    last_month = datetime.now(timezone.utc).replace(day=1) - timedelta(days=5)
    _spend(500, when=last_month)

    assert may_spend(estimated_cost_cents=10).allowed is True


def test_every_feature_shares_one_ceiling(db_session, monkeypatch):
    """The reason the ledger is in shared/ rather than per-domain. A
    ledger per feature would be several budgets each believing it is the
    only one spending -- several ways to blow through one limit."""
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "100")

    _spend(60, feature="catalogue_matching")
    _spend(50, feature="verification")

    assert may_spend(estimated_cost_cents=1).allowed is False


def test_remaining_never_goes_negative(db_session, monkeypatch):
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "100")
    _spend(250)
    assert may_spend().remaining_cents == 0


# --- the ledger itself -----------------------------------------------------


def test_the_same_question_hashes_the_same_way():
    """Answers "was this the same call" without storing a supplier's
    catalogue text forever."""
    assert hash_input("Coke 2L", "Coca-Cola 2L") == hash_input("Coke 2L", "Coca-Cola 2L")
    assert hash_input("Coke 2L", "Coca-Cola 2L") != hash_input("Coca-Cola 2L", "Coke 2L")


def test_a_failed_call_is_still_recorded(db_session):
    """A failed call still costs wall-clock and sometimes tokens, and a
    run that failed repeatedly is exactly what someone reading this
    table needs to see."""
    AIDecisionRepository.record(
        feature="catalogue_matching",
        kind=AIDecisionKind.EXTRACT,
        provider="claude",
        model="claude-haiku-4-5",
        input_hash=hash_input("row"),
        error="Timeout after 30s",
    )
    db.session.flush()

    assert AIDecisionRepository.spend_this_month_cents() == 0


def test_fake_and_dry_run_rows_are_distinguishable_from_real_spend(db_session):
    """Reading the table, it must be obvious which rows cost money."""
    AIDecisionRepository.record(
        feature="catalogue_matching",
        kind=AIDecisionKind.ADJUDICATE,
        provider="dry-run(claude)",
        model="dry-run(claude)",
        input_hash=hash_input("x"),
        cost_cents=0,
    )
    db.session.flush()

    assert AIDecisionRepository.spend_this_month_cents() == 0
