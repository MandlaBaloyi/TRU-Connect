"""
Finance Engine exceptions.

Deliberately does NOT inherit from src.core.exceptions.AppError: AppError
carries HTTP status codes and API-envelope concerns, which are a web
layer concept. The Finance Engine has no idea it's being called from an
HTTP request -- it might be called from a scheduled job, a CLI tool, or
a test. Domains catch these and translate them into whatever their own
transport needs.
"""

from __future__ import annotations


class FinanceError(Exception):
    """Base for every Finance Engine error."""


class UnknownCurrencyError(FinanceError):
    """A currency code the engine has no definition for."""


class CurrencyMismatchError(FinanceError):
    """
    Arithmetic attempted between two different currencies.

    Deliberately an ERROR, never an implicit conversion: silently
    converting ZAR + USD using some assumed rate would produce a
    confident, wrong number -- exactly the kind of failure that erodes
    trust in every figure the platform shows. Conversion, when it
    exists, will be an explicit call through future/exchange.py.
    """


class InvalidAmountError(FinanceError):
    """An amount that isn't a whole number of minor units, or isn't a
    number at all."""


class NegativeAmountError(FinanceError):
    """A negative amount where the caller required a non-negative one."""


class MoneyOverflowError(FinanceError):
    """An amount beyond the safe representable range -- see
    constants.MAX_SAFE_MINOR_UNITS for why this bound exists."""


class AllocationError(FinanceError):
    """An allocation that cannot be satisfied (e.g. splitting into zero
    or negative parts)."""


class ParseError(FinanceError):
    """Human-entered text that couldn't be understood as an amount."""
