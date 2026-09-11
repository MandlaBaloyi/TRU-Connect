"""
Finance Engine constants.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Safe representable range
# ---------------------------------------------------------------------------
# Postgres BIGINT tops out at 9_223_372_036_854_775_807, so the database
# is not the binding constraint here -- JavaScript is.
#
# Every amount this engine produces eventually crosses a JSON boundary to
# the React Native app, and JavaScript's `number` type can only represent
# integers exactly up to 2**53 - 1 (Number.MAX_SAFE_INTEGER). Beyond that,
# JSON.parse silently returns a DIFFERENT number -- no error, no warning,
# just a wrong amount. Capping here means the engine refuses to produce a
# value that would be silently corrupted in transit, rather than the
# corruption surfacing as an inexplicable figure on someone's phone.
#
# For scale: in ZAR cents this is roughly R90 trillion, far beyond any
# real TruConnect value. This bound exists to make an entire failure
# mode impossible, not because it's expected to be approached.
MAX_SAFE_MINOR_UNITS = 2**53 - 1
MIN_SAFE_MINOR_UNITS = -(2**53 - 1)

# ---------------------------------------------------------------------------
# Formatting defaults (South African conventions -- see formatter.py)
# ---------------------------------------------------------------------------
DEFAULT_THOUSANDS_SEPARATOR = "\u00a0"  # non-breaking space: "R 1 250.00"
DEFAULT_DECIMAL_SEPARATOR = "."
