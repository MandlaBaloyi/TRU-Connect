"""
Core -- what money IS, and how it is calculated, formatted, parsed and
validated. The heart of the Finance Engine.

    money.py         the Money value object (integer minor units, immutable)
    currency.py      Currency definitions; minor_units drives all precision
    constants.py     safe ranges and formatting defaults
    exceptions.py    the engine's error hierarchy
    rounding.py      rounding strategies (Decimal-based, never float)
    calculations.py  add/subtract/multiply/percentage/total
    allocation.py    splitting and payment allocation without losing cents
    formatter.py     Money -> human-readable text
    parser.py        human-entered text -> Money
    validation.py    what money values are allowed
"""
