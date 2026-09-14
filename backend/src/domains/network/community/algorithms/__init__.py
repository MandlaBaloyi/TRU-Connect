"""
MOVED to src/shared/algorithms/ and re-exported here.

My Connections needs the same reorder-gap computation the feed does, and
a domain may not import the composer (see
tests/architecture/test_community_is_a_composer.py). So the functions
moved somewhere both can reach.

This re-export keeps the feed's own imports and its tests unchanged.
New callers OUTSIDE this package must import src.shared.algorithms
directly -- reaching for this path would be importing the composer,
which is the thing the architecture test exists to stop.
"""
from src.shared.algorithms import distance, reorder_gap  # noqa: F401

__all__ = ["distance", "reorder_gap"]
