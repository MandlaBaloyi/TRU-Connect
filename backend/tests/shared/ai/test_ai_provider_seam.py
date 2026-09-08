"""
The AI provider seam: what it costs, what it sends, and what it does by
default.

THE POINT OF MOST OF THESE TESTS IS THAT NOTHING HAPPENS. Three separate
environment values must be changed deliberately before a single paid
call is possible, and each is checked independently -- so forgetting one
leaves the system safe rather than spending. Several tests below assert
exactly that, because a default that quietly spent money would be
discovered on an invoice.

NO NETWORK, NO KEY, NO COST. The Claude provider is never constructed
here; only the fake, and the composition logic that decides between
them.
"""
from __future__ import annotations

import pytest

from src.shared.ai.config import ai_config
from src.shared.ai.errors import AIProviderNotConfiguredError
from src.shared.ai.providers.composition import (
    DryRunProvider,
    get_ai_provider,
    reset_ai_providers,
)
from src.shared.ai.providers.fake_provider import FakeAIProvider


@pytest.fixture(autouse=True)
def _clean_providers(monkeypatch):
    """Every test starts from clean, unmemoised providers and a clean
    environment -- same reasoning as reset_media_provider."""
    for name in (
        "AI_PROVIDER",
        "AI_DRY_RUN",
        "AI_MONTHLY_BUDGET_CENTS",
        "AI_EXTRACTION_MODEL",
        "AI_ADJUDICATION_MODEL",
        "AI_ADJUDICATION_EFFORT",
    ):
        monkeypatch.delenv(name, raising=False)
    reset_ai_providers()
    yield
    reset_ai_providers()


# --- the defaults are free -------------------------------------------------


def test_the_default_provider_is_the_fake():
    """Nothing configured means nothing billable. This is the first of
    the three independent guards."""
    assert ai_config.provider_name() == "fake"
    assert isinstance(get_ai_provider(), FakeAIProvider)


def test_dry_run_is_on_by_default():
    """The second guard. Even a correctly configured Claude provider
    sends nothing until this is explicitly turned off."""
    assert ai_config.is_dry_run() is True


def test_the_budget_is_zero_by_default():
    """The third guard. Zero means no paid calls at all, so the ceiling
    is not merely low -- it is closed."""
    assert ai_config.monthly_budget_cents() == 0


def test_all_three_guards_are_independent(monkeypatch):
    """Turning one off must not turn the others off. This is why they
    are separate values rather than one flag: forgetting one leaves the
    system safe."""
    monkeypatch.setenv("AI_PROVIDER", "claude")
    assert ai_config.is_dry_run() is True
    assert ai_config.monthly_budget_cents() == 0


# --- composition -----------------------------------------------------------


def test_off_raises_rather_than_silently_doing_nothing():
    """A caller is entitled to know the tier is unavailable, and it can
    handle that by using the free tiers -- which is what it should do
    anyway."""
    import os

    os.environ["AI_PROVIDER"] = "off"
    try:
        with pytest.raises(AIProviderNotConfiguredError):
            get_ai_provider()
    finally:
        os.environ.pop("AI_PROVIDER", None)


def test_an_unknown_provider_name_raises_rather_than_defaulting(monkeypatch):
    """Quietly falling back to SOME provider for an unrecognised name is
    exactly the "bad configuration does something surprising" failure
    this arrangement exists to prevent."""
    monkeypatch.setenv("AI_PROVIDER", "gpt-please")
    with pytest.raises(AIProviderNotConfiguredError):
        get_ai_provider()


def test_the_fake_is_memoised_but_resettable():
    assert get_ai_provider() is get_ai_provider()
    reset_ai_providers()
    assert get_ai_provider() is not None


# --- dry run ---------------------------------------------------------------


def test_dry_run_adjudication_is_uncertain_never_confident():
    """A dry run must never cause an auto-link -- nothing actually
    judged the pair. Returning False would be worse still: that is a
    claim, and a dry run is entitled to make none."""
    from src.shared.ai.providers.composition import DryRunProvider

    wrapped = DryRunProvider(FakeAIProvider())
    result = wrapped.adjudicate(instruction="", left="Coke 2L", right="Coke 2L")

    assert result.confidence == 0.5, "0.5 lands in the review band, not the auto-link band"
    assert result.same is False
    assert "Dry run" in result.reason


def test_dry_run_never_calls_the_wrapped_provider():
    inner = FakeAIProvider()
    wrapped = DryRunProvider(inner)

    wrapped.extract(instruction="", text="Coke 2L", schema={})
    wrapped.adjudicate(instruction="", left="a", right="b")

    assert inner.calls == [], "a dry run that reached the provider is not a dry run"


# --- the fake ---------------------------------------------------------------


def test_the_fake_is_deterministic():
    """A test that passes today must not fail on Tuesday."""
    provider = FakeAIProvider()
    first = provider.adjudicate(instruction="", left="Coke 2L", right="Coke 2L")
    second = provider.adjudicate(instruction="", left="Coke 2L", right="Coke 2L")
    assert (first.same, first.confidence) == (second.same, second.confidence)


def test_the_fake_reports_no_cost():
    """A budget test that accidentally billed real money would be worse
    than no budget test."""
    provider = FakeAIProvider()
    result = provider.adjudicate(instruction="", left="a", right="b")
    assert result.usage.cost_cents == 0


def test_an_unprogrammed_fake_is_uncertain_rather_than_wrong():
    """Uncertain sends a row to the review queue, which is the safe
    direction. A fake that guessed would let a test pass because the
    fake was helpful rather than because the code was right."""
    provider = FakeAIProvider()
    result = provider.adjudicate(instruction="", left="Coke 2L", right="Fanta 500ml")
    assert result.same is False
    assert result.confidence == 0.5


def test_the_fake_can_be_programmed():
    provider = FakeAIProvider()
    provider.queue_adjudication(same=True, confidence=0.97, reason="pinned")

    result = provider.adjudicate(instruction="", left="anything", right="anything else")

    assert result.same is True
    assert result.confidence == 0.97


def test_an_unprogrammed_extraction_returns_nothing_rather_than_inventing():
    provider = FakeAIProvider()
    assert provider.extract(instruction="", text="COKE 2LT", schema={}).data == {}


# --- costing ---------------------------------------------------------------


def test_cost_is_computed_from_real_token_counts():
    """Haiku at 100 cents per million input tokens: a million input
    tokens is one dollar."""
    assert ai_config.cost_cents("claude-haiku-4-5", input_tokens=1_000_000, output_tokens=0) == 100


def test_cached_input_is_charged_at_a_tenth():
    """Which is why caching the taxonomy prefix across thousands of rows
    is worth doing."""
    full = ai_config.cost_cents("claude-haiku-4-5", input_tokens=1_000_000, output_tokens=0)
    cached = ai_config.cost_cents(
        "claude-haiku-4-5", input_tokens=0, output_tokens=0, cached_input_tokens=1_000_000
    )
    assert cached * 10 == full


def test_cost_rounds_up_so_small_calls_cannot_drift_past_a_ceiling():
    """A few thousand sub-cent calls rounding down would let real spend
    sail past a budget that believes it has not been reached."""
    assert ai_config.cost_cents("claude-haiku-4-5", input_tokens=1, output_tokens=1) == 1


def test_a_free_call_costs_nothing():
    assert ai_config.cost_cents("claude-haiku-4-5", input_tokens=0, output_tokens=0) == 0


def test_an_unknown_model_prices_as_the_most_expensive_known_one():
    """Over-estimating stops early; under-estimating does not stop at
    all. A new model id nobody added must never consume the budget at
    zero."""
    unknown = ai_config.cost_cents("claude-something-new", input_tokens=0, output_tokens=1_000_000)
    opus = ai_config.cost_cents("claude-opus-5", input_tokens=0, output_tokens=1_000_000)
    assert unknown == opus


def test_the_models_come_from_the_environment(monkeypatch):
    assert ai_config.extraction_model() == "claude-haiku-4-5"
    assert ai_config.adjudication_model() == "claude-sonnet-5"

    monkeypatch.setenv("AI_ADJUDICATION_MODEL", "claude-opus-5")
    assert ai_config.adjudication_model() == "claude-opus-5"


def test_a_malformed_budget_falls_back_rather_than_crashing(monkeypatch):
    monkeypatch.setenv("AI_MONTHLY_BUDGET_CENTS", "twenty rand")
    assert ai_config.monthly_budget_cents() == 0
