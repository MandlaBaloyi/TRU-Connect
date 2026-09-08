"""
AI configuration, read from the environment.

EVERY DEFAULT COSTS NOTHING. AI_PROVIDER defaults to "fake",
AI_MONTHLY_BUDGET_CENTS defaults to 0, and AI_DRY_RUN defaults to true.
THREE separate values must be changed deliberately before a single paid
call can happen, and each of them is checked independently -- so
forgetting one leaves the system safe rather than spending.

That is not a temporary arrangement while money is tight. The
deterministic tiers of matching are meant to carry most rows
permanently; the paid tier is the tail. A default that spent money would
invert that.

THE PRICE TABLE IS HERE, NOT IN THE PROVIDER, and it is deliberately
data rather than logic: the provider computes what a call cost by
looking it up, and when prices change this is the one place to edit.
Rates are per MILLION tokens, in US cents, matching how they are
published.
"""
from __future__ import annotations

import os

#: Published rates per MILLION tokens, in US cents.
#: (input, output, cached-input). Cached input is roughly a tenth of
#: normal input, which is why the taxonomy prefix is worth caching.
_PRICE_PER_MTOK_CENTS = {
    "claude-haiku-4-5": (100, 500, 10),
    "claude-sonnet-5": (200, 1000, 20),
    "claude-opus-5": (500, 2500, 50),
}


def _int_env(name: str, default: int) -> int:
    """A malformed value falls back rather than crashing the app at
    import time -- a typo in an env var must never be why the backend
    will not boot."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def provider_name() -> str:
    """"fake" (default), "claude", or "off".

    "off" and "fake" differ: off raises so a caller learns the tier is
    unavailable; fake answers deterministically so tests can exercise
    the code around it."""
    return os.environ.get("AI_PROVIDER", "fake").strip().lower()


def is_dry_run() -> bool:
    """Log what WOULD be sent, and what it would cost, without sending.

    DEFAULT TRUE, so even a correctly configured Claude provider sends
    nothing until this is explicitly turned off. It exists so the bill
    can be measured before it is paid."""
    return os.environ.get("AI_DRY_RUN", "true").lower() != "false"


def monthly_budget_cents() -> int:
    """The hard ceiling. 0 -- the default -- means no paid calls at all.

    EXCEEDING IT IS NOT AN ERROR. It means fall back to the free tiers:
    running out of money degrades completeness, never correctness, and
    never breaks an import. See AIBudgetExceededError's own docstring."""
    return max(0, _int_env("AI_MONTHLY_BUDGET_CENTS", 0))


def extraction_model() -> str:
    """Reading a line and filling in fields is extraction, not
    judgement, so the cheapest capable model is the right one. Batching
    halves it again."""
    return os.environ.get("AI_EXTRACTION_MODEL", "claude-haiku-4-5")


def adjudication_model() -> str:
    """"Are these the same product?" is judgement, and a wrong answer
    makes a price comparison a lie -- so this is where the money should
    go if there is any.

    SONNET RATHER THAN OPUS BY DEFAULT, chosen deliberately. Because the
    gate is on CONFIDENCE rather than on model, a less certain model
    produces more review-queue items rather than more wrong matches: the
    cost of going cheaper is completeness, not accuracy. That makes the
    model a dial, and this is the setting to raise first when there is
    budget and the queue is uselessly long."""
    return os.environ.get("AI_ADJUDICATION_MODEL", "claude-sonnet-5")


def adjudication_effort() -> str:
    """low | medium | high | xhigh | max. Higher effort thinks longer
    and costs more."""
    return os.environ.get("AI_ADJUDICATION_EFFORT", "high").strip().lower()


def price_for(model: str) -> tuple[int, int, int]:
    """(input, output, cached-input) cents per million tokens.

    An unknown model prices as the most expensive one known rather than
    as free. A new model id that nobody added here must not silently
    consume the budget at zero and blow straight through the ceiling --
    over-estimating stops early, under-estimating does not stop at all.
    """
    if model in _PRICE_PER_MTOK_CENTS:
        return _PRICE_PER_MTOK_CENTS[model]
    return max(_PRICE_PER_MTOK_CENTS.values(), key=lambda rates: rates[1])


def cost_cents(
    model: str, *, input_tokens: int, output_tokens: int, cached_input_tokens: int = 0
) -> int:
    """What a call cost, in whole cents, ROUNDED UP.

    Rounding up rather than to nearest is deliberate: a few thousand
    sub-cent calls rounding down would let real spend drift past a
    ceiling that believes it has not been reached.
    """
    input_rate, output_rate, cached_rate = price_for(model)
    millicents = (
        input_tokens * input_rate
        + output_tokens * output_rate
        + cached_input_tokens * cached_rate
    )
    # Rates are per million tokens, so divide by 1_000_000 -- ceiling
    # division, hence the +999_999.
    return (millicents + 999_999) // 1_000_000 if millicents else 0
