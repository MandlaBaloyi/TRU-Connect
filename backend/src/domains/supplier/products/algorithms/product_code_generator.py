"""
Generates the short, human-readable, PLATFORM-WIDE unique code every
product gets -- shown to both the supplier and any business ordering
from them, in place of ever showing this row's own internal UUID
anywhere a human reads or types it.

FORMAT: TRU-XXXXXX -- 6 characters drawn from a 32-symbol alphabet
that deliberately EXCLUDES 0/O and 1/I, since this is meant to be read
aloud or typed by hand and those pairs are easy to misread. 32^6 is a
little over 1 billion possible codes.

UNIQUENESS IS A GUARANTEE, NOT A PROBABILITY -- every generated code is
checked against the database before being accepted (ProductRepository.
product_code_exists, which includes soft-deleted rows on purpose: a
code must never be reissued to a different product just because the
original was deleted -- an old order or report referencing that code
should never later point at something else). A collision is
astronomically unlikely at this address space; if one happens, this
simply tries again rather than accepting a duplicate.

ENTERPRISE-INTEGRATION READY BY DESIGN -- this is the ONE place code
generation happens, and product_code is stored as a plain string
column with no assumption baked in about who produced it. A future
enterprise supplier needing their own external numbering scheme
instead of this one means changing what happens INSIDE
generate_product_code, not any of its callers.
"""
from __future__ import annotations

import secrets

from src.domains.supplier.products.repositories.product_repository import ProductRepository

# Deliberately excludes 0/O and 1/I -- meant to be read aloud or typed
# by hand without ambiguity.
_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_CODE_LENGTH = 6
_MAX_ATTEMPTS = 10


def generate_product_code() -> str:
    for _ in range(_MAX_ATTEMPTS):
        suffix = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))
        candidate = f"TRU-{suffix}"
        if not ProductRepository.product_code_exists(candidate):
            return candidate

    # Astronomically unlikely at this address space (32^6 is just over
    # 1 billion) -- if this ever actually fires, it's a sign something
    # is structurally wrong (e.g. the collision check itself broke),
    # not ordinary bad luck worth silently retrying forever.
    raise RuntimeError("Could not generate a unique product code after multiple attempts.")
