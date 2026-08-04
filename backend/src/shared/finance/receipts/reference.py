"""
Receipt reference generation -- short, human-speakable identifiers.

DESIGN CONSTRAINT that shapes everything here: a reference must be
readable ALOUD over a phone call. When a customer with a feature phone
disputes an amount, the resolution path is the business owner reading
the reference aloud, or looking it up in the app themselves. That rules
out long hashes, and rules out characters that sound or look alike.
"""

from __future__ import annotations

import re

# Excludes I, O, 0, 1 -- indistinguishable when spoken or handwritten,
# which matters precisely because these get read aloud and copied by hand.
SPEAKABLE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_NON_ALNUM = re.compile(r"[^A-Z0-9]")

REFERENCE_LENGTH = 6


def build_reference(prefix: str, source_id: str) -> str:
    """
    Derive a stable reference from an existing id.

    build_reference("LB", "entry-a1b2c3d4") -> "LB-A1B2C3"

    DERIVED, never randomly generated and stored separately: a reference
    computed from the record it points at can never drift out of sync
    with that record, and needs no extra database column.
    """
    cleaned = _NON_ALNUM.sub("", source_id.upper())
    if not cleaned:
        raise ValueError(f"Cannot build a reference from {source_id!r}")
    tail = cleaned[-REFERENCE_LENGTH:].rjust(REFERENCE_LENGTH, "0")
    return f"{prefix.upper()}-{tail}"


def is_valid_reference(reference: str, prefix: str | None = None) -> bool:
    """Shape check only. Proves NOTHING about authenticity -- that needs
    signing.py, which is deliberately not implemented."""
    if not reference or "-" not in reference:
        return False
    ref_prefix, _, tail = reference.partition("-")
    if prefix is not None and ref_prefix != prefix.upper():
        return False
    return len(tail) == REFERENCE_LENGTH and tail.isalnum() and tail.isupper()
