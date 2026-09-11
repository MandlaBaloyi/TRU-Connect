"""
Shared rendering for terminal output.

EXTRACTED FROM catalogue.py, where these lived as private helpers
until a second command family needed them. They are here rather than
duplicated because the AGREEMENT RENDERING in particular is not
cosmetic -- see _agreement below. A second copy that drifted would
silently change what a reviewer believes they are looking at.
"""
from __future__ import annotations


def pct(value) -> str:
    """A 0-1 score as a percentage, or "-" when there is no score."""
    return "-" if value is None else f"{float(value) * 100:.0f}%"


def agreement(value) -> str:
    """True / False / None, rendered so the THIRD state is visible.

    None means "no signal", never "disagreed" -- the distinction the
    whole matching domain is built on. A product with no brand is not
    a product whose brand was wrong. Printing None as blank or as "no"
    would erase exactly the thing a reviewer needs to see, and would do
    it invisibly: the screen would look complete.
    """
    if value is True:
        return "yes"
    if value is False:
        return "NO"
    return "n/a"


def render_evidence(evidence: dict) -> str:
    """The evidence dict as aligned lines, sorted for a stable reading
    order -- the same field appears in the same place every time, so a
    reviewer working a queue can scan rather than re-read."""
    if not evidence:
        return "      (no evidence recorded -- this row predates the evidence column)"
    lines = []
    for key, value in sorted(evidence.items()):
        if key in ("brand_agrees", "pack_agrees"):
            shown = agreement(value)
        elif key == "text_similarity":
            shown = pct(value)
        elif isinstance(value, bool):
            shown = "yes" if value else "no"
        else:
            shown = str(value)
        lines.append(f"      {key:24} {shown}")
    return "\n".join(lines)
