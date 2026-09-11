# TruConnect Finance Engine

The platform's financial integrity engine. Every feature that creates,
calculates, validates, formats, or stores money uses this module.

    Loan Book / Supplier Payments / TRU Wallet / Financing / Settlement
                              |
                              v
                      Shared Finance Engine

## Quick start

```python
from src.shared.finance import Money, add, format_amount, parse_amount, validate_payment

sale = Money(50000)                       # R500.00, as integer cents
payment = parse_amount("R 200,50")        # handles real SA input
remaining = subtract(sale, payment)
print(format_amount(remaining))           # "R 299.50"
```

## What this engine owns

| Package | Responsibility |
|---|---|
| `core/` | What money IS; calculation, formatting, parsing, validation |
| `receipts/` | Receipt MECHANICS (references, QR, signing) -- never content |
| `reconciliation/` | Pure matching/balancing algorithms (not built yet) |
| `future/` | Reserved, deliberately empty |

## What it must NEVER own

Authentication, permissions, fraud detection, rate limiting, audit,
monitoring, gateway integration, or any domain's business logic.

**This is enforced, not just documented.** `tests/architecture/test_finance_boundaries.py`
parses every file in the engine with Python's AST and fails the build if
any of these appear:

- an import from `src.domains.*`
- an import from `src.shared.{audit,security,queue,email,monitoring,cache}`
- an import of `flask` or `sqlalchemy`
- a call to `float()`

Run it: `pytest tests/architecture/ -v`

The tests were verified to genuinely fail: a file deliberately violating
all five rules was added, all five tests failed with messages naming the
exact file, line, and reason -- then it was removed.

## Two levels of use

**Level 1** -- every money module: validation, calculation, formatting,
allocation, audit, atomic transactions.

**Level 2** -- REAL MONEY MOVEMENT only (Wallet, Supplier Payments,
Settlement): fraud detection, velocity limits, gateway callbacks,
reconciliation, payment authorization.

**LOAN BOOK IS LEVEL 1 ONLY.** It records debt between two people; it
never moves money, so Level 2 machinery does not apply and must not be
bolted onto it.

## Core guarantees, all verified by tests

**Integer minor units, always.** Never a float, at any layer. `Money`
rejects floats at construction; `multiply`/`percentage` reject float
factors; `round_to_minor_units` rejects floats; the architecture test
bans `float()` calls entirely.

**Precision comes from the currency, not a global constant.** ZAR has 2
decimal places, JPY has 0, BHD has 3 -- `Currency.minor_units` drives
every calculation and format, so no `/100` assumption exists anywhere.
Tested against all three.

**Allocation never loses a cent.** Splitting R100 three ways gives
[3334, 3333, 3333] = exactly 10000, not 9999. The largest-remainder
method guarantees parts always sum back to the original. Verified across
13 parametrized cases including 1 cent split 3 ways and prime ratios.

**Currency mismatches raise, never silently convert.** Adding ZAR to USD
is an error, not an assumed exchange rate.

**Amounts are bounded by JavaScript's safe integer range** (2^53-1), not
Postgres BIGINT -- because every amount eventually crosses a JSON
boundary to the React Native app, where a larger value would be silently
corrupted by `JSON.parse` with no error.

## Test suite

84 tests, all passing:

```
pytest tests/ -v
```

- `tests/architecture/` (5) -- boundary enforcement
- `tests/shared/finance/test_money_core.py` (16) -- construction, precision, rejections
- `tests/shared/finance/test_allocation.py` (22) -- cent-loss guarantees
- `tests/shared/finance/test_calculations.py` (~20) -- arithmetic, rounding, validation
- `tests/shared/finance/test_formatting_parsing.py` (~21) -- SA input formats, round-trips

## What is NOT implemented, deliberately

`receipts/signing.py`, `receipts/qr.py`, `receipts/verification.py` all
raise `NotImplementedError` with an explanation. Real signing needs a
server-held private key with real key management, plus a verification
endpoint -- none of which exists yet. **A signature that can be forged is
worse than no signature**, because it invites people to trust a document
that hasn't been verified. Loan Book's receipts currently carry a plain
reference code and make no authenticity claim anywhere in their wording.

`reconciliation/` and `future/` are empty for the same reason: nothing
to reconcile until real money movement exists.

## Next step

Nothing imports this engine yet. The next piece of work is Loan Book's
backend, which will be its first consumer -- and the frontend's existing
`formatCents`/`parseRandsToCents` should eventually be replaced by a
TypeScript mirror of this module so both sides share identical rules.
