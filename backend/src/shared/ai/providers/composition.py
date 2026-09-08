"""
get_ai_provider() -- the ONE place that decides which provider answers.

Every caller uses this function, never FakeAIProvider() or
ClaudeAIProvider() directly, exactly as get_media_provider() and
get_payment_provider() already establish in this codebase.

THE "NO KEY CAN BREAK ANYTHING" GUARANTEE LIVES HERE, not just in a
docstring. ClaudeAIProvider is imported INSIDE the branch that needs it,
so a backend running on the fake never imports the anthropic package,
never reads an API key, and never validates one. A missing, empty or
malformed credential has zero effect on anything -- including the
backend's ability to boot -- which is the same protection composition.py
in orders/providers gives manual checkout against a bad PayFast config.

DRY RUN IS A WRAPPER, NOT A FLAG INSIDE EACH PROVIDER. Wrapping means
there is exactly one implementation of "log what this would cost and
send nothing", it applies to every provider automatically, and no
provider can forget to check.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.shared.ai.config import ai_config
from src.shared.ai.errors import AIProviderNotConfiguredError
from src.shared.ai.providers.provider import (
    AdjudicationResult,
    AIProvider,
    AIUsage,
    ExtractionResult,
)

logger = logging.getLogger(__name__)

_fake_provider: AIProvider | None = None
_claude_provider: AIProvider | None = None


class DryRunProvider(AIProvider):
    """Logs the intent and the estimated cost; sends nothing.

    ADJUDICATION RETURNS UNCERTAINTY, deliberately -- confidence 0.5,
    which the matching gate treats as "a human decides". A dry run must
    never cause an auto-link, because nothing actually judged the pair.
    Returning False would be worse still: that is a claim, and a dry run
    is entitled to make none.
    """

    def __init__(self, wrapped: AIProvider) -> None:
        self._wrapped = wrapped

    @property
    def name(self) -> str:
        return f"dry-run({self._wrapped.name})"

    def extract(
        self,
        *,
        instruction: str,
        text: str,
        schema: Dict[str, Any],
        images: Optional[List[bytes]] = None,
    ) -> ExtractionResult:
        logger.info("AI DRY RUN extract: would send %d chars to %s", len(text or ""), self._wrapped.name)
        return ExtractionResult(data={}, usage=AIUsage(model=self.name))

    def adjudicate(
        self,
        *,
        instruction: str,
        left: str,
        right: str,
        images: Optional[List[bytes]] = None,
    ) -> AdjudicationResult:
        logger.info("AI DRY RUN adjudicate: %r vs %r via %s", left, right, self._wrapped.name)
        return AdjudicationResult(
            same=False,
            confidence=0.5,
            reason="Dry run -- no model was consulted.",
            usage=AIUsage(model=self.name),
        )


def get_ai_provider() -> AIProvider:
    """The provider for this environment.

    Raises rather than silently defaulting when AI_PROVIDER names
    something unknown. Quietly falling back to SOME provider for an
    unrecognised name is exactly the "bad configuration does something
    surprising" failure this whole arrangement exists to prevent -- and
    the caller can handle the raise by using the free tiers, which is
    what it should do anyway.
    """
    global _fake_provider, _claude_provider

    name = ai_config.provider_name()

    if name == "off":
        raise AIProviderNotConfiguredError("AI_PROVIDER is off.")

    if name == "fake":
        if _fake_provider is None:
            from src.shared.ai.providers.fake_provider import FakeAIProvider

            _fake_provider = FakeAIProvider()
        return _fake_provider

    if name == "claude":
        if _claude_provider is None:
            # Imported HERE and nowhere else. A backend on the fake never
            # loads the anthropic package at all.
            from src.shared.ai.providers.claude_provider import ClaudeAIProvider

            _claude_provider = ClaudeAIProvider()
        provider: AIProvider = _claude_provider
        # The wrap is applied on every call rather than memoised, so
        # flipping AI_DRY_RUN takes effect without a restart.
        return DryRunProvider(provider) if ai_config.is_dry_run() else provider

    raise AIProviderNotConfiguredError(f"Unknown AI_PROVIDER: {name!r}")


def reset_ai_providers() -> None:
    """Test-only -- lets each test start from clean instances rather than
    ones memoised across the session, same reasoning as
    reset_media_provider and reset_payment_providers."""
    global _fake_provider, _claude_provider
    _fake_provider = None
    _claude_provider = None
