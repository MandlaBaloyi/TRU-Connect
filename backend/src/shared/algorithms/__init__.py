"""
Pure computations that more than one domain needs.

WHY THESE LEFT network/community/algorithms/. They were written for the
Community feed and lived inside it, which was right until a second
caller appeared: My Connections needs the same reorder gap to say "you
usually reorder from Sipho about now".

The feed is a COMPOSER -- it reads from domains and no domain may read
from it, enforced by tests/architecture/test_community_is_a_composer.py
-- so `connections` importing the feed would have failed the build. That
test's own failure message names this exact remedy: move the function
somewhere both can import, do not import the composer.

NOTHING HERE MAY IMPORT A DOMAIN. These take plain values -- a list of
datetimes, a pair of coordinates -- and return plain values. That is
what makes them safe to share, and it is the property to preserve: the
moment one of them needs a repository it belongs in a domain again.


GROUPED BY WHAT THEY COMPUTE, NOT BY WHO CALLS THEM. `geo` is distance
and location maths; `trading` is what a pair's order history says about
how they trade. Naming a folder after a consumer -- `community/` was
considered -- would quietly re-couple these to the domain they were just
moved out of, and the next reader would assume the feed owns them again.

    geo/      distance
    trading/  reorder_gap
"""
from src.shared.algorithms.geo import distance  # noqa: F401
from src.shared.algorithms.trading import reorder_gap  # noqa: F401

__all__ = ["distance", "geo", "reorder_gap", "trading"]
