"""
Order reference generation -- TRU-{supplier_code}-{6 random chars}.

Two genuinely different jobs, kept separate on purpose (confirmed
directly during planning, after an earlier version of this design
tried to fold a date and a sequential count into the reference itself
and both were removed for real reasons):

- supplier_code (4 chars, assigned once, see supplier_code_generator.py)
  scopes a lookup to one supplier's own namespace immediately, without
  scanning every other supplier's orders first -- both a real
  performance win and a real IDOR-safety one, the same "never trust
  find-anything-anywhere, always scope the lookup" discipline already
  applied everywhere else in this codebase.

- The 6 random characters are the ENTIRE security guarantee of the
  reference. Nothing else in this string does any guess-resistance
  work -- the supplier_code repeats across every order that supplier
  ever receives, so it carries no per-order secrecy at all. This is
  exactly why the format was deliberately kept free of anything
  guessable or sequential: a business's own order count, or a date, or
  anything counted, would let an outsider infer real business volume
  just by comparing two references, without ever seeing the orders
  themselves.

secrets, not random -- same reasoning as the supplier code's own
generator: this needs to be genuinely unguessable, not just
statistically unlikely to repeat.
"""
from __future__ import annotations

import secrets

_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_SUFFIX_LENGTH = 6
_MAX_ATTEMPTS = 10


def generate_order_reference(supplier_code: str) -> str:
    """A single, random reference for this supplier -- NOT guaranteed
    unique on its own. See generate_unique_order_reference for the
    real, database-checked version."""
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(_SUFFIX_LENGTH))
    return f"TRU-{supplier_code}-{suffix}"


def generate_unique_order_reference(supplier_code: str) -> str:
    """The REAL, safe version. 36^6 (minus excluded characters) is
    over a billion possible suffixes per supplier -- a genuine
    collision is astronomically unlikely, but this never trusts that
    alone; a real unique constraint on the column is the actual
    guarantee, this is just what avoids hitting it in normal
    operation."""
    from src.domains.network.orders.models.stock_order import StockOrder

    for _ in range(_MAX_ATTEMPTS):
        reference = generate_order_reference(supplier_code)
        if not StockOrder.query.filter_by(order_reference=reference).first():
            return reference

    raise RuntimeError(f"Could not generate a unique order reference after {_MAX_ATTEMPTS} attempts.")
