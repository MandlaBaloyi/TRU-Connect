"""
Errors from the AI layer.

DELIBERATELY NOT AppError SUBCLASSES. src/shared/ may not depend on
domains, and more importantly an AI failure is almost never something a
USER should see: a matching call that fails should leave a row
unmatched, not fail a supplier's import. Callers catch these and degrade;
they do not propagate them to an HTTP response.
"""
from __future__ import annotations


class AIError(Exception):
    """Base for everything this layer raises."""


class AIProviderNotConfiguredError(AIError):
    """No usable provider -- missing key, unknown provider name.

    Raised at CALL time rather than at import, so a backend with no AI
    configured still boots and serves every other request normally."""


class AIBudgetExceededError(AIError):
    """The monthly ceiling is spent.

    NOT A FAILURE CONDITION, and callers must not treat it as one. It
    means "fall back to the free tiers", which is the entire point of
    having a ceiling: running out of money degrades completeness, never
    correctness, and never breaks an import."""


class AICallFailedError(AIError):
    """The provider was reached and could not answer -- timeout, rate
    limit, malformed response. Same handling as a budget stop: degrade to
    the free tiers and carry on."""
