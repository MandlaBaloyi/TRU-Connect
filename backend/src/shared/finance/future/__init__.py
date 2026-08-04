"""
Reserved for capabilities NOT built yet.

    interest.py     -- interest calculation (Lending domain, future)
    tax.py          -- VAT/tax calculation
    exchange.py     -- currency conversion
    settlement.py   -- settlement calculations
    commissions.py  -- platform commission calculations
    billing.py      -- billing cycles

DELIBERATELY EMPTY, not stubbed. Placeholder functions that raise would
still appear in autocomplete and invite someone to "just fill this in
quickly" without the design work each actually needs.

NOTE FOR WHOEVER IMPLEMENTS THESE: they will NOT all graduate to the
same place. interest.py and tax.py are Level 1 calculations and likely
belong in core/. exchange.py is its own concern, with its own rate-source
and staleness questions. settlement.py and commissions.py are Level 2
and likely split domain/engine the way reconciliation does. Don't assume
"everything in future/ moves into core/".
"""
