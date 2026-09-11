"""
The Money value object -- what money IS in TruConnect.

THREE PROPERTIES, ALL DELIBERATE:

1. INTEGER MINOR UNITS ONLY. Money is stored as a whole number of a
   currency's smallest unit (cents for ZAR), never as a float. Floats
   cannot represent every decimal fraction exactly -- 0.1 + 0.2 famously
   isn't 0.3 -- and those tiny errors compound across many transactions
   until a shop owner's total is a cent off. A shop owner spotting
   "my total is wrong by 1c" destroys trust in every other number the
   app shows.

2. CURRENCY-CARRYING. Every Money knows its own currency, even though
   TruConnect is ZAR-only today. A bare number can be added to any
   other bare number; a Money can only be added to Money of the SAME
   currency, enforced below. That makes cross-currency bugs impossible
   rather than merely unlikely, and costs nothing to add now versus an
   enormous retrofit later.

3. IMMUTABLE. Operations return NEW Money objects; nothing is ever
   mutated in place. An amount that can be silently changed after
   validation is an amount you cannot reason about -- immutability means
   a validated Money stays validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Union

from src.shared.finance.core.constants import MAX_SAFE_MINOR_UNITS, MIN_SAFE_MINOR_UNITS
from src.shared.finance.core.currency import DEFAULT_CURRENCY, Currency
from src.shared.finance.core.exceptions import (
    CurrencyMismatchError,
    InvalidAmountError,
    MoneyOverflowError,
    NegativeAmountError,
)


@dataclass(frozen=True)
class Money:
    """
    An exact amount in a specific currency.

    `minor_units` is the whole-number amount in the currency's smallest
    unit -- cents for ZAR, yen for JPY (which has no subunit), fils for
    BHD. Never a float, never a major-unit value.
    """

    minor_units: int
    currency: Currency = DEFAULT_CURRENCY

    def __post_init__(self) -> None:
        # bool is a subclass of int in Python -- excluded explicitly,
        # since Money(True) silently becoming 1 cent would be absurd.
        if isinstance(self.minor_units, bool) or not isinstance(self.minor_units, int):
            raise InvalidAmountError(
                f"minor_units must be a whole number of minor units, got "
                f"{self.minor_units!r} ({type(self.minor_units).__name__}). "
                f"Floats are rejected on purpose -- see this module's docstring."
            )
        if not (MIN_SAFE_MINOR_UNITS <= self.minor_units <= MAX_SAFE_MINOR_UNITS):
            raise MoneyOverflowError(
                f"{self.minor_units} is outside the safe representable range "
                f"(±{MAX_SAFE_MINOR_UNITS}); see constants.MAX_SAFE_MINOR_UNITS."
            )

    # --- Constructors ---------------------------------------------------

    @classmethod
    def zero(cls, currency: Currency = DEFAULT_CURRENCY) -> "Money":
        return cls(0, currency)

    @classmethod
    def from_major_units(
        cls, amount: Union[int, str, Decimal], currency: Currency = DEFAULT_CURRENCY
    ) -> "Money":
        """
        Build from a major-unit value (rands, dollars) -- e.g. "12.50" ->
        1250 cents.

        Accepts str/Decimal/int but NOT float, deliberately: passing
        12.50 as a float has already lost exactness before this function
        ever sees it, so accepting it would only launder an error that
        already happened. Callers with user input should use
        formatting.parser.parse_amount() instead.
        """
        if isinstance(amount, float):
            raise InvalidAmountError(
                "from_major_units() rejects float. Pass a str or Decimal "
                "(e.g. '12.50'), or use parser.parse_amount() for user input -- "
                "a float has already lost exactness before arriving here."
            )
        try:
            decimal_amount = Decimal(amount)
        except Exception as exc:  # noqa: BLE001
            raise InvalidAmountError(f"Cannot interpret {amount!r} as an amount") from exc

        scaled = decimal_amount * currency.subunit_factor
        if scaled != scaled.to_integral_value():
            raise InvalidAmountError(
                f"{amount} has more precision than {currency.code} supports "
                f"({currency.minor_units} decimal place(s))."
            )
        return cls(int(scaled), currency)

    # --- Introspection --------------------------------------------------

    @property
    def is_zero(self) -> bool:
        return self.minor_units == 0

    @property
    def is_positive(self) -> bool:
        return self.minor_units > 0

    @property
    def is_negative(self) -> bool:
        return self.minor_units < 0

    def to_major_units(self) -> Decimal:
        """Exact major-unit value as a Decimal (never a float) -- for
        display and serialization only, never for further arithmetic."""
        return Decimal(self.minor_units) / Decimal(self.currency.subunit_factor)

    def require_non_negative(self) -> "Money":
        """Assert non-negativity, returning self for chaining. Used by
        callers where a negative amount is a genuine error (a credit sale
        of -R50 is meaningless), rather than banning negatives engine-wide
        -- reversals and corrections legitimately need them."""
        if self.is_negative:
            raise NegativeAmountError(f"Amount must not be negative, got {self}")
        return self

    # --- Guards ---------------------------------------------------------

    def _assert_same_currency(self, other: "Money") -> None:
        if self.currency.code != other.currency.code:
            raise CurrencyMismatchError(
                f"Cannot combine {self.currency.code} with {other.currency.code}. "
                f"Conversion must be explicit -- see future/exchange.py."
            )

    # --- Comparison -----------------------------------------------------

    def __lt__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.minor_units < other.minor_units

    def __le__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.minor_units <= other.minor_units

    def __gt__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.minor_units > other.minor_units

    def __ge__(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.minor_units >= other.minor_units

    def __repr__(self) -> str:
        return f"Money({self.minor_units}, {self.currency.code})"

    def __str__(self) -> str:
        # Intentionally minimal -- real presentation belongs to
        # formatting.formatter, which knows about separators and symbols.
        return f"{self.currency.code} {self.to_major_units()}"
