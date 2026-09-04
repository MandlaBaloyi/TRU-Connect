"""
Supplier code generation -- a real, permanent identity assigned once
per supplier, the first half of every order reference they'll ever
receive (see domains/network/orders' own order_reference_generator.py
for how the two combine).

4 random characters, using Python's secrets module specifically --
never `random`, which is not cryptographically secure and is the
wrong tool the moment "hard to guess" is a real requirement, not a
nice-to-have. Confirmed directly during planning: this needs to be
genuinely unguessable, since the whole point is letting a supplier
trust that an order reference containing their own code could only
have come from a real order routed to them, not something a business
made up or found by guessing.

Deliberately excludes ambiguous characters (0/O, 1/I/L) -- this is
meant to eventually be human-visible (a supplier's own reference,
shown on their account), and a code someone could misread over the
phone or when typing it back in defeats its own purpose.
"""
from __future__ import annotations

import secrets

# 0, O, 1, I, L excluded -- see this module's own docstring.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_LENGTH = 4
_MAX_ATTEMPTS = 10


def generate_supplier_code() -> str:
    """A single, random 4-character code -- NOT guaranteed unique on
    its own. See generate_unique_supplier_code for the real,
    database-checked version every real caller should use instead."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(_LENGTH))


def generate_unique_supplier_code() -> str:
    """The REAL, safe version -- checks the actual database before
    returning, retrying on the astronomically unlikely chance of a
    collision (36^4 minus the excluded characters is still well over
    a million possible codes). Never trusts the odds alone; a real
    unique constraint on the column is the actual guarantee, this is
    just what avoids hitting it in normal operation."""
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile

    for _ in range(_MAX_ATTEMPTS):
        code = generate_supplier_code()
        if not SupplierProfile.query.filter_by(supplier_code=code).first():
            return code

    raise RuntimeError(f"Could not generate a unique supplier code after {_MAX_ATTEMPTS} attempts.")
