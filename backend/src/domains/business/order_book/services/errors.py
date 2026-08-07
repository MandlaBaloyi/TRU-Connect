"""
Order Book service-layer exceptions.

OrderBookNotFoundError is used for BOTH "genuinely doesn't exist" and
"exists but belongs to a different business" -- deliberately the same
exception, carrying no information that would let a caller distinguish
the two. Same reasoning as Loan Book's LoanBookNotFoundError: an
attacker probing IDs must never be able to tell "wrong ID" from
"someone else's real ID" apart from the response.
"""
from __future__ import annotations


class OrderBookError(Exception):
    """Base for every Order Book service error."""


class OrderBookNotFoundError(OrderBookError):
    """Order/customer either doesn't exist, is deleted, or doesn't
    belong to the requesting business -- see module docstring."""


class OrderBookValidationError(OrderBookError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


class OrderBookInvalidTransitionError(OrderBookError):
    """Raised when an order's status transition isn't allowed -- e.g.
    completing an already-cancelled order. Matches the frontend's
    'INVALID_TRANSITION' mock error code."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
