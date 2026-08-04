"""
TRU Connect Finance Engine -- the platform's financial integrity engine.

Every feature that creates, calculates, validates, formats, or stores
money uses THIS module. No feature implements its own money logic.

    Loan Book / Supplier Payments / TRU Wallet / Financing / Settlement
                              |
                              v
                      Shared Finance Engine

WHAT THIS ENGINE OWNS
    core/            what money IS, how it's calculated, formatted,
                     parsed, and validated
    receipts/        receipt MECHANICS -- references, QR payloads,
                     signatures, verification (never receipt CONTENT,
                     which each domain owns -- see receipts/__init__.py)
    reconciliation/  pure matching/balancing algorithms
    future/          reserved, deliberately empty

WHAT THIS ENGINE MUST NEVER OWN
    Authentication, permissions, fraud detection, rate limiting, audit,
    monitoring, gateway integration, or ANY domain's business logic.

    Those belong to the domains and to the other shared platform
    engines. This boundary is not merely documented -- it is ENFORCED by
    tests/architecture/test_finance_boundaries.py, which fails the build
    if any file under shared/finance/ imports domains.*, shared.audit.*,
    shared.security.*, or shared.queue.*.

    That test exists because a documented rule decays: someone rushing a
    feature adds "just one import", nobody notices in review, and six
    months later Finance depends on Loan Book while Loan Book depends on
    Finance. The test makes that impossible rather than discouraged.

TWO LEVELS OF USE (architecture rule)
    Level 1 -- every money module: validation, calculation, formatting,
        allocation, audit, atomic transactions.
    Level 2 -- REAL MONEY MOVEMENT only (Wallet, Supplier Payments,
        Settlement): fraud detection, velocity limits, gateway
        callbacks, reconciliation, payment authorization.

    LOAN BOOK IS LEVEL 1 ONLY. It records debt between two people; it
    never moves money, so Level 2 machinery does not apply and must not
    be bolted onto it.

INTEGER MINOR UNITS, ALWAYS
    Money is a whole number of a currency's smallest unit (cents for
    ZAR) -- never a float, at any layer, ever. See core/money.py.
"""

from __future__ import annotations

from src.shared.finance.core.currency import (
    DEFAULT_CURRENCY,
    ZAR,
    Currency,
    get_currency,
    is_supported,
)
from src.shared.finance.core.money import Money
from src.shared.finance.core.exceptions import (
    AllocationError,
    CurrencyMismatchError,
    FinanceError,
    InvalidAmountError,
    MoneyOverflowError,
    NegativeAmountError,
    ParseError,
    UnknownCurrencyError,
)
from src.shared.finance.core.calculations import (
    absolute,
    add,
    is_greater,
    is_less,
    max_of,
    min_of,
    multiply,
    negate,
    percentage,
    subtract,
    total,
)
from src.shared.finance.core.allocation import (
    allocate_to_debts,
    split_by_ratios,
    split_evenly,
    unallocated_remainder,
)
from src.shared.finance.core.rounding import DEFAULT_ROUNDING, RoundingMode, round_to_minor_units
from src.shared.finance.core.formatter import format_amount, format_compact, format_for_json
from src.shared.finance.core.parser import parse_amount
from src.shared.finance.core.validation import (
    ValidationResult,
    require_non_negative,
    require_positive,
    validate_non_negative,
    validate_payment,
    validate_positive,
    validate_within,
)

__all__ = [
    "Money", "Currency", "ZAR", "DEFAULT_CURRENCY", "get_currency", "is_supported",
    "add", "subtract", "negate", "absolute", "total", "multiply", "percentage",
    "min_of", "max_of", "is_greater", "is_less",
    "split_evenly", "split_by_ratios", "allocate_to_debts", "unallocated_remainder",
    "RoundingMode", "DEFAULT_ROUNDING", "round_to_minor_units",
    "format_amount", "format_compact", "format_for_json", "parse_amount",
    "ValidationResult", "validate_positive", "validate_non_negative",
    "validate_within", "validate_payment", "require_positive", "require_non_negative",
    "FinanceError", "UnknownCurrencyError", "CurrencyMismatchError",
    "InvalidAmountError", "NegativeAmountError", "MoneyOverflowError",
    "AllocationError", "ParseError",
]
