"""
Receipt data assembly for the Loan Book -- the backend counterpart to
the frontend's receiptService.ts.

Uses shared.finance.receipts.reference.build_reference() for the
reference code (already built, already tested -- short, speakable,
excludes ambiguous characters) rather than reinventing it here.

DELIBERATELY NO SIGNING/QR HERE EITHER, same reasoning as the frontend
and as shared/finance/receipts/signing.py's own docstring: real signing
needs server-held key management that doesn't exist yet, and a
forgeable signature is worse than none. This returns the same
plain-reference-code receipt the frontend already builds -- the backend
version exists so a future server-rendered receipt (e.g. for a web
share link) can produce byte-identical content to the mobile app's own
receipt, not because it does anything the frontend doesn't already do.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from src.domains.business.loan_book.services.loan_book_service import LoanEntryView
from src.shared.finance import Money, format_amount
from src.shared.finance.receipts.reference import build_reference


@dataclass
class ReceiptData:
    reference_code: str
    customer_name: str
    from_label: str
    sale_date_label: str
    description: Optional[str]
    original_amount_label: str
    amount_paid_label: str
    outstanding_amount_label: str
    is_settled: bool
    is_partly_paid: bool


def build_from_label(owner_first_name: Optional[str]) -> str:
    """Mirrors the frontend's buildFromLabel() exactly -- same fallback,
    same reasoning: never fabricate a business name that doesn't exist
    yet (no Business Profile feature), always supply what's real."""
    trimmed = (owner_first_name or "").strip()
    if not trimmed:
        return "Sent via TruConnect"
    return f"{trimmed}'s shop"


def build_receipt_data(
    view: LoanEntryView, customer_name: str, owner_first_name: Optional[str] = None
) -> ReceiptData:
    original = view.entry.original_amount_cents
    return ReceiptData(
        reference_code=build_reference("LB", str(view.entry.id)),
        customer_name=customer_name,
        from_label=build_from_label(owner_first_name),
        # NOT "%-d" -- that flag is Linux/Mac-only and raises ValueError
        # on Windows strftime, which is what this backend actually runs
        # on. lstrip("0") gets the same "3 August 2026" (not "03 August
        # 2026") result portably.
        sale_date_label=view.entry.sale_date.strftime("%d %B %Y").lstrip("0"),
        description=view.entry.description,
        original_amount_label=format_amount(Money(original)),
        amount_paid_label=format_amount(view.amount_paid),
        outstanding_amount_label=format_amount(view.outstanding),
        is_settled=view.entry.is_settled,
        is_partly_paid=view.amount_paid.is_positive and view.outstanding.is_positive,
    )
