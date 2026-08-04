"""
Currency definitions.

WHY minor_units LIVES ON THE CURRENCY, not as a global constant:
"1 unit = 100 minor units" is true for ZAR and USD, but it is NOT
universal -- JPY has no minor unit at all (minor_units=0), and BHD/KWD
use three (1 dinar = 1000 fils). Hard-coding `precision = 2` anywhere in
this engine would silently produce wrong results the first time a
non-2-decimal currency appears, and retrofitting it later means auditing
every calculation, formatter, and stored value in the platform.

Defining it here costs almost nothing today and makes that entire class
of bug impossible.

TRU Connect is ZAR-only today. The non-ZAR entries below are NOT a claim
that those currencies are supported -- they exist so the precision logic
is exercised by real varied values in tests rather than being untested
theory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.shared.finance.core.exceptions import UnknownCurrencyError


@dataclass(frozen=True)
class Currency:
    """
    Immutable currency definition.

    minor_units: how many decimal places this currency subdivides into.
        2 -> 1 ZAR = 100 cents
        0 -> 1 JPY = 1 yen (no subdivision)
        3 -> 1 BHD = 1000 fils
    """

    code: str
    name: str
    symbol: str
    minor_units: int

    @property
    def subunit_factor(self) -> int:
        """How many minor units make one major unit: 10 ** minor_units.
        ZAR -> 100, JPY -> 1, BHD -> 1000."""
        return 10**self.minor_units


ZAR = Currency(code="ZAR", name="South African Rand", symbol="R", minor_units=2)

# Present ONLY so precision logic is tested against genuinely different
# minor_units values rather than assumed. Not a support claim.
USD = Currency(code="USD", name="US Dollar", symbol="$", minor_units=2)
JPY = Currency(code="JPY", name="Japanese Yen", symbol="¥", minor_units=0)
BHD = Currency(code="BHD", name="Bahraini Dinar", symbol="BD", minor_units=3)

_REGISTRY: Dict[str, Currency] = {c.code: c for c in (ZAR, USD, JPY, BHD)}

DEFAULT_CURRENCY = ZAR


def get_currency(code: str) -> Currency:
    """Look up a currency by ISO code. Raises rather than defaulting --
    a silently-wrong currency is worse than a loud failure."""
    try:
        return _REGISTRY[code.upper()]
    except KeyError:
        raise UnknownCurrencyError(f"Unknown currency code: {code!r}") from None


def is_supported(code: str) -> bool:
    return code.upper() in _REGISTRY
