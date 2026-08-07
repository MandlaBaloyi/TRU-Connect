"""
Loan Book service-layer exceptions.

LoanBookNotFoundError is used for BOTH "genuinely doesn't exist" and
"exists but belongs to a different business" -- deliberately the same
exception, carrying no information that would let a caller distinguish
the two. The API layer turns this into a plain 404 either way. This is
the actual authorization mechanism, not a courtesy: an attacker probing
IDs must never be able to tell "wrong ID" from "someone else's real ID"
apart from the response.
"""
from __future__ import annotations


class LoanBookError(Exception):
    """Base for every Loan Book service error."""


class LoanBookNotFoundError(LoanBookError):
    """Customer/entry either doesn't exist, is deleted, or doesn't
    belong to the requesting business -- see module docstring."""


class LoanBookValidationError(LoanBookError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field
