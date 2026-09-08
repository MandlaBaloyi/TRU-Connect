"""
Matching configuration, read from the environment.

EVERY DEFAULT IS FREE. MATCHING_MODE defaults to "deterministic", which
runs tiers 0 to 3 -- barcode, learned alias, normalised exact, and rules
plus trigram -- and never calls a model or spends a cent. Turning the
paid tier on requires deliberately setting a value, so the
accidental-spend path does not exist.

That is not a temporary arrangement for a tight month. The deterministic
tiers are meant to carry most rows permanently, and every rule added to
algorithms/pack_size.py or every brand alias added to the catalogue
removes rows from the paid tier for good. The AI is the tail, not the
engine.

WHY THE THRESHOLDS ARE CONFIGURABLE AND THE TIERS ARE NOT. What counts
as "confident enough to link without a human" is a business risk
decision that will move as the catalogue proves itself -- start
cautious, loosen when the review queue shows the auto-links were right.
Which tiers exist, and in what order, is architecture and belongs in
code.
"""
from __future__ import annotations

import os


def _float_env(name: str, default: float) -> float:
    """A malformed value falls back to the default rather than crashing
    the app at import time. A typo in an env var must never be the
    reason the backend will not boot -- same reasoning as bulk_import's
    own config."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def is_matching_enabled() -> bool:
    """The whole-feature kill switch, mirroring
    BULK_IMPORT_ENABLED -- a no-deploy way to stop matching platform
    wide if it is ever doing something wrong at scale. Off means offers
    simply stay unmatched, which is exactly how every offer behaves
    today."""
    return os.environ.get("MATCHING_ENABLED", "true").lower() != "false"


def use_ai_tier() -> bool:
    """Whether tier 4 (extraction and adjudication by model) may run.

    DEFAULT FALSE. "full" is the only value that turns it on, and even
    then shared/ai's own budget ceiling and dry-run switch still apply
    on top -- three independent things must agree before a paid call is
    made.
    """
    return os.environ.get("MATCHING_MODE", "deterministic").lower() == "full"


def auto_link_threshold() -> float:
    """At or above this, link without asking anyone.

    0.92 is deliberately high. The cost of a wrong auto-link is that
    TRU Connect tells a business "R89 here, R74 there" about two
    different products -- the catalogue breaking the one promise it
    exists to make. The cost of being too cautious is a longer review
    queue, which is merely work.
    """
    return _float_env("MATCHING_AUTO_LINK_CONFIDENCE", 0.92)


def review_threshold() -> float:
    """At or above this but below auto-link, a human decides.

    Below it there is no plausible candidate at all, so a new catalogue
    product is created rather than a reviewer being handed a question
    with no good answer.
    """
    return _float_env("MATCHING_REVIEW_CONFIDENCE", 0.70)
