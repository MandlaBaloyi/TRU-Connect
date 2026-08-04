"""
Validation -- what money values are allowed.

Returns RESULT OBJECTS rather than raising, for the same reason Loan
Book's own validators do: a validation failure is an expected, routine
outcome (a user typing too much) that the UI needs to display next to a
field, not an exceptional condition. Raising for something that happens
every day makes callers wrap everything in try/except and turns normal
flow into exception handling.

The `require_*` helpers below DO raise, for the cases where a violation
means a programming error rather than user input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.shared.finance.core.exceptions import NegativeAmountError
from src.shared.finance.core.money import Money


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    message: Optional[str] = None

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(True)

    @classmethod
    def fail(cls, message: str) -> "ValidationResult":
        return cls(False, message)


def validate_positive(amount: Money) -> ValidationResult:
    """For amounts that must be greater than zero -- a credit sale of R0
    or -R50 is meaningless."""
    if amount.is_negative:
        return ValidationResult.fail("Amount cannot be negative.")
    if amount.is_zero:
        return ValidationResult.fail("Enter an amount greater than zero.")
    return ValidationResult.ok()


def validate_non_negative(amount: Money) -> ValidationResult:
    """For amounts where zero is legitimate (a settled balance)."""
    if amount.is_negative:
        return ValidationResult.fail("Amount cannot be negative.")
    return ValidationResult.ok()


def validate_within(amount: Money, maximum: Money) -> ValidationResult:
    """
    For amounts bounded by another amount -- e.g. a payment that must
    not exceed what's actually owed. Messages stay plain-language, since
    they're shown directly to a shop owner (Doc 02 §14).
    """
    amount._assert_same_currency(maximum)
    if amount > maximum:
        from src.shared.finance.core.formatter import format_amount

        return ValidationResult.fail(f"That's more than the {format_amount(maximum)} owed.")
    return ValidationResult.ok()


def validate_payment(amount: Money, outstanding: Money) -> ValidationResult:
    """Convenience: a payment must be positive and not exceed the debt."""
    positive = validate_positive(amount)
    if not positive.is_valid:
        return positive
    return validate_within(amount, outstanding)


# --- Raising variants, for programmer-error cases ----------------------


def require_positive(amount: Money) -> Money:
    result = validate_positive(amount)
    if not result.is_valid:
        raise NegativeAmountError(result.message)
    return amount


def require_non_negative(amount: Money) -> Money:
    return amount.require_non_negative()
