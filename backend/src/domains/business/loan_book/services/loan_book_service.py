"""
Loan Book business operations.

THE AUTHORIZATION PATTERN, applied consistently everywhere in this
file: every method that touches an existing customer or entry takes
business_id as a REQUIRED parameter and calls the repository's
get_by_id(id, business_id) -- which returns None for "doesn't exist" and
"exists but isn't yours" identically (see repositories' docstrings).
This service turns that None into LoanBookNotFoundError uniformly. There
is no code path anywhere in this file that loads a row by ID alone and
checks ownership afterward -- ownership is baked into the fetch itself,
which is what makes it structurally hard to accidentally bypass by
forgetting a check, the classic shape of a real IDOR bug.

MONEY: every amount is a shared.finance.Money instance from the moment
it enters this file to the moment it leaves. The outstanding balance on
an entry is NEVER stored -- it's derived fresh from the entry's original
amount minus the sum of its real payments, every time, using
shared.finance.subtract()/total(). This exactly mirrors the frontend's
balanceCalculator.ts, so a shop owner's balance can never silently drift
between what the app shows and what the database would compute if asked
directly.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from src.domains.business.loan_book.models.customer import Customer
from src.domains.business.loan_book.models.loan_entry import LoanEntry
from src.domains.business.loan_book.models.loan_history_event import LoanHistoryEvent, LoanHistoryEventType
from src.domains.business.loan_book.models.payment import Payment
from src.domains.business.loan_book.repositories.customer_repository import CustomerRepository
from src.domains.business.loan_book.repositories.history_repository import HistoryRepository
from src.domains.business.loan_book.repositories.loan_repository import LoanRepository
from src.domains.business.loan_book.repositories.payment_repository import PaymentRepository
from src.domains.business.loan_book.services.errors import LoanBookNotFoundError, LoanBookValidationError
from src.extensions import db
from src.shared.finance import Money, subtract, total, validate_payment, validate_positive


logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record_history(
    business_id: uuid.UUID,
    customer_id: uuid.UUID,
    event_type: LoanHistoryEventType,
    *,
    loan_entry_id: Optional[uuid.UUID] = None,
    amount: Optional[Money] = None,
    description: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """
    NEVER THROWS, and never poisons the caller's own transaction --
    same reasoning already established for the Auth audit system
    (shared/audit.py's publish()): recording history must never break
    the action being recorded. A lost history row is survivable; a
    credit sale failing to save because ITS OWN history entry failed to
    save would be a much worse outcome.

    RUNS IN A SAVEPOINT (db.session.begin_nested()), not a plain
    try/except around a flush in the OUTER transaction. This matters:
    every caller of this function has already flushed its own primary
    write (the new customer, entry, or payment) in the SAME session
    before calling this. A bare `except: db.session.rollback()` would
    discard that already-flushed primary write too -- silently, since
    the caller's code continues past the swallowed exception and
    reaches its own commit() with nothing left to commit. A SAVEPOINT
    means only the failed history INSERT gets undone; everything
    flushed before it in the outer transaction survives for the
    caller's own commit() to persist normally.

    Caught and fixed by reproducing the real bug (a Postgres enum
    value mismatch) against a real migration-shaped schema, not
    assumed -- see git history / the migration fix alongside this file.
    """
    try:
        with db.session.begin_nested():
            HistoryRepository.append(LoanHistoryEvent(
                id=uuid.uuid4(),
                business_id=business_id,
                customer_id=customer_id,
                loan_entry_id=loan_entry_id,
                event_type=event_type,
                amount_cents=amount.minor_units if amount is not None else None,
                description=description,
                reason=reason,
            ))
    except Exception:  # noqa: BLE001
        logger.warning("Failed to record loan book history event", exc_info=True)


@dataclass
class LoanEntryView:
    """The API/service-layer answer to 'how much is still owed on this
    entry' -- outstanding is ALWAYS derived here, never read from a
    stored column, matching balanceCalculator.ts exactly."""

    entry: LoanEntry
    payments: List[Payment]
    outstanding: Money
    amount_paid: Money


def _derive_view(entry: LoanEntry, payments: List[Payment]) -> LoanEntryView:
    original = Money(entry.original_amount_cents)
    paid = total([Money(p.amount_cents) for p in payments], currency=original.currency)
    outstanding = subtract(original, paid)
    # A payment can never legitimately exceed the debt (enforced at
    # record_payment time below) -- clamping here is a second, cheap
    # guard against outstanding ever reading as negative regardless.
    if outstanding.is_negative:
        outstanding = Money.zero(original.currency)
    return LoanEntryView(entry=entry, payments=payments, outstanding=outstanding, amount_paid=paid)


class LoanBookService:
    # --- Customers ------------------------------------------------------

    @staticmethod
    def create_customer(
        business_id: uuid.UUID,
        name: str,
        phone: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
    ) -> Customer:
        """customer_id accepts an optional CLIENT-SUPPLIED id -- the
        frontend already generates its own UUIDs offline-first
        (generateId() in loanBookApi.ts); accepting that same id here,
        rather than always generating a new server-side one, is what
        lets a record created offline reconcile to the exact same row
        once synced, instead of creating a duplicate."""
        if not name or not name.strip():
            raise LoanBookValidationError("Customer name is required.", field="name")

        now = _now()
        customer = Customer(
            id=customer_id or uuid.uuid4(),
            business_id=business_id,
            name=name.strip(),
            phone=phone.strip() if phone else None,
            first_recorded_at=now,
            last_transaction_at=now,
        )
        CustomerRepository.create(customer)
        _record_history(business_id, customer.id, LoanHistoryEventType.CUSTOMER_CREATED)
        db.session.commit()
        return customer

    @staticmethod
    def get_customer(business_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        customer = CustomerRepository.get_by_id(customer_id, business_id)
        if customer is None:
            raise LoanBookNotFoundError("Customer not found.")
        return customer

    @staticmethod
    def list_customers(business_id: uuid.UUID) -> List[Customer]:
        return CustomerRepository.list_for_business(business_id)

    # --- Loan entries -----------------------------------------------------

    @staticmethod
    def create_entry(
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        amount: Money,
        description: Optional[str] = None,
        sale_date: Optional[datetime] = None,
        entry_id: Optional[uuid.UUID] = None,
    ) -> LoanEntry:
        # Ownership check happens by construction: get_customer() can
        # only ever return a customer that belongs to business_id, so a
        # caller cannot create an entry against someone else's customer
        # even by supplying a real customer_id they don't own.
        customer = LoanBookService.get_customer(business_id, customer_id)

        result = validate_positive(amount)
        if not result.is_valid:
            raise LoanBookValidationError(result.message, field="amount")

        now = _now()
        entry = LoanEntry(
            id=entry_id or uuid.uuid4(),
            business_id=business_id,  # copied from the AUTHORIZED business_id, never trusted from elsewhere
            customer_id=customer.id,
            original_amount_cents=amount.minor_units,
            sale_date=sale_date or now,
            description=description.strip() if description else None,
            is_settled=False,
        )
        LoanRepository.create(entry)
        _record_history(
            business_id, customer.id, LoanHistoryEventType.SALE_CREATED,
            loan_entry_id=entry.id, amount=amount, description=entry.description,
        )

        customer.last_transaction_at = now
        db.session.commit()
        return entry

    @staticmethod
    def get_entry(business_id: uuid.UUID, entry_id: uuid.UUID) -> LoanEntryView:
        entry = LoanRepository.get_by_id(entry_id, business_id)
        if entry is None:
            raise LoanBookNotFoundError("Entry not found.")
        payments = PaymentRepository.list_for_entry(entry.id)
        return _derive_view(entry, payments)

    @staticmethod
    def list_entries(business_id: uuid.UUID) -> List[LoanEntryView]:
        entries = LoanRepository.list_for_business(business_id)
        if not entries:
            return []
        payments = PaymentRepository.list_for_entries([e.id for e in entries])
        by_entry: dict[uuid.UUID, List[Payment]] = {}
        for p in payments:
            by_entry.setdefault(p.loan_entry_id, []).append(p)
        return [_derive_view(e, by_entry.get(e.id, [])) for e in entries]

    @staticmethod
    def delete_entry(business_id: uuid.UUID, entry_id: uuid.UUID, reason: Optional[str] = None) -> None:
        entry = LoanRepository.get_by_id(entry_id, business_id)
        if entry is None:
            raise LoanBookNotFoundError("Entry not found.")
        entry.is_deleted = True
        entry.deleted_at = _now()
        entry.deletion_reason = reason
        _record_history(
            business_id, entry.customer_id, LoanHistoryEventType.ENTRY_DELETED,
            loan_entry_id=entry.id, reason=reason,
        )
        db.session.commit()

    # --- Payments -----------------------------------------------------

    @staticmethod
    def record_payment(
        business_id: uuid.UUID,
        entry_id: uuid.UUID,
        amount: Money,
        note: Optional[str] = None,
        paid_at: Optional[datetime] = None,
        payment_id: Optional[uuid.UUID] = None,
    ) -> LoanEntryView:
        # Same ownership-by-construction pattern as create_entry(): this
        # can only ever load an entry the caller's own business owns.
        view = LoanBookService.get_entry(business_id, entry_id)

        result = validate_payment(amount, view.outstanding)
        if not result.is_valid:
            raise LoanBookValidationError(result.message, field="amount")

        now = _now()
        payment = Payment(
            id=payment_id or uuid.uuid4(),
            loan_entry_id=view.entry.id,
            amount_cents=amount.minor_units,
            paid_at=paid_at or now,
            note=note.strip() if note else None,
        )
        PaymentRepository.create(payment)
        _record_history(
            business_id, view.entry.customer_id, LoanHistoryEventType.PAYMENT_RECORDED,
            loan_entry_id=view.entry.id, amount=amount,
        )

        new_outstanding = subtract(view.outstanding, amount)
        if new_outstanding.is_zero:
            view.entry.is_settled = True
            view.entry.settled_at = now

        db.session.commit()
        return LoanBookService.get_entry(business_id, entry_id)

    @staticmethod
    def delete_payment(business_id: uuid.UUID, entry_id: uuid.UUID, payment_id: uuid.UUID) -> LoanEntryView:
        """Ownership enforced via the SAME get_entry() call every other
        payment-touching method uses -- a payment can only ever be
        deleted through an entry the caller's own business owns."""
        view = LoanBookService.get_entry(business_id, entry_id)
        target = next((p for p in view.payments if p.id == payment_id), None)
        if target is None:
            raise LoanBookNotFoundError("Payment not found.")

        PaymentRepository.delete(target)
        _record_history(
            business_id, view.entry.customer_id, LoanHistoryEventType.PAYMENT_REMOVED,
            loan_entry_id=view.entry.id, amount=Money(target.amount_cents),
        )

        # Re-derive settlement status -- removing a payment can un-settle
        # an entry that was previously fully paid.
        remaining_payments = [p for p in view.payments if p.id != payment_id]
        remaining_view = _derive_view(view.entry, remaining_payments)
        if not remaining_view.outstanding.is_zero:
            view.entry.is_settled = False
            view.entry.settled_at = None

        db.session.commit()
        return LoanBookService.get_entry(business_id, entry_id)

    # --- Restore / soft-delete lifecycle -------------------------------

    @staticmethod
    def restore_entry(business_id: uuid.UUID, entry_id: uuid.UUID) -> LoanEntry:
        """Restores an entry that was deleted independently (not as
        part of a customer cascade) -- or one that WAS cascade-deleted
        but whose customer has since also been restored. Only entries
        still owned by business_id can ever be found here; a deleted
        row belonging to another business is exactly as invisible as an
        active one."""
        entry = LoanEntry.query.filter_by(
            id=entry_id, business_id=business_id, is_deleted=True
        ).first()
        if entry is None:
            raise LoanBookNotFoundError("Entry not found in trash.")
        entry.is_deleted = False
        entry.deleted_at = None
        entry.deletion_reason = None
        _record_history(business_id, entry.customer_id, LoanHistoryEventType.ENTRY_RESTORED, loan_entry_id=entry.id)
        db.session.commit()
        return entry

    @staticmethod
    def delete_customer(business_id: uuid.UUID, customer_id: uuid.UUID, reason: Optional[str] = None) -> None:
        """
        Soft-deletes the customer AND cascades to their currently-open
        entries -- mirrors the frontend's MockDataRepository.softDeleteCustomer()
        exactly, including the cascade-marker mechanism: entries swept
        in by this cascade get the SAME deleted_at timestamp as the
        customer, which is what lets restore_customer() below know
        precisely which entries to bring back (and which to leave
        alone, if they were independently deleted at a different time).
        """
        customer = CustomerRepository.get_by_id(customer_id, business_id)
        if customer is None:
            raise LoanBookNotFoundError("Customer not found.")

        now = _now()
        customer.is_deleted = True
        customer.deleted_at = now
        customer.deletion_reason = reason

        open_entries = LoanRepository.list_for_customer(customer_id, business_id)
        for entry in open_entries:
            entry.is_deleted = True
            entry.deleted_at = now  # shared cascade marker -- see docstring
            entry.deletion_reason = f"Customer removed: {reason}" if reason else "Customer removed"

        _record_history(business_id, customer.id, LoanHistoryEventType.CUSTOMER_DELETED, reason=reason)
        db.session.commit()

    @staticmethod
    def restore_customer(business_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        customer = Customer.query.filter_by(
            id=customer_id, business_id=business_id, is_deleted=True
        ).first()
        if customer is None:
            raise LoanBookNotFoundError("Customer not found in trash.")

        cascade_marker = customer.deleted_at
        customer.is_deleted = False
        customer.deleted_at = None
        customer.deletion_reason = None

        # Only restore entries stamped with the SAME deletion timestamp
        # -- i.e. ones that went into trash as PART OF THIS CASCADE, not
        # an entry independently deleted at some other time.
        cascaded_entries = LoanEntry.query.filter_by(
            customer_id=customer_id, business_id=business_id, is_deleted=True, deleted_at=cascade_marker
        ).all()
        for entry in cascaded_entries:
            entry.is_deleted = False
            entry.deleted_at = None
            entry.deletion_reason = None

        _record_history(business_id, customer.id, LoanHistoryEventType.CUSTOMER_RESTORED)
        db.session.commit()
        return customer

    @staticmethod
    def get_trash(business_id: uuid.UUID) -> dict:
        """Mirrors the frontend's getTrash(): deleted customers get
        their own summary row; deleted entries only appear separately
        when their OWN customer is currently active (not itself
        deleted) -- see loan_repository/customer_repository for the
        exact filtering this depends on."""
        deleted_customers = CustomerRepository.list_deleted_for_business(business_id)
        deleted_customer_ids = {c.id for c in deleted_customers}

        all_deleted_entries = LoanRepository.list_deleted_for_business(business_id)
        independent_entries = [
            e for e in all_deleted_entries if e.customer_id not in deleted_customer_ids
        ]

        customer_summaries = []
        for customer in deleted_customers:
            all_entries = LoanRepository.list_for_customer_including_deleted(customer.id, business_id)
            payments = PaymentRepository.list_for_entries([e.id for e in all_entries])
            by_entry: dict[uuid.UUID, List[Payment]] = {}
            for p in payments:
                by_entry.setdefault(p.loan_entry_id, []).append(p)
            views = [_derive_view(e, by_entry.get(e.id, [])) for e in all_entries]
            customer_summaries.append({
                "customer": customer,
                "open_entry_count": sum(1 for v in views if v.outstanding.is_positive),
                "total_entry_count": len(views),
                "total_outstanding": total([v.outstanding for v in views]) if views else Money.zero(),
            })

        return {"customers": customer_summaries, "entries": independent_entries}

    # --- Customer aggregate view (customer-first list) ------------------

    @staticmethod
    def get_customer_view(business_id: uuid.UUID, customer_id: uuid.UUID) -> dict:
        customer = LoanBookService.get_customer(business_id, customer_id)
        entries = LoanRepository.list_for_customer(customer_id, business_id)
        payments = PaymentRepository.list_for_entries([e.id for e in entries])
        by_entry: dict[uuid.UUID, List[Payment]] = {}
        for p in payments:
            by_entry.setdefault(p.loan_entry_id, []).append(p)
        views = [_derive_view(e, by_entry.get(e.id, [])) for e in entries]
        outstanding_total = total([v.outstanding for v in views]) if views else Money.zero()
        return {
            "customer": customer,
            "entries": views,
            "total_outstanding": outstanding_total,
            "open_entry_count": sum(1 for v in views if v.outstanding.is_positive),
            "has_overdue": False,  # overdue-threshold logic lives with aging, not this view
        }

    @staticmethod
    def list_customer_views(business_id: uuid.UUID) -> List[dict]:
        customers = CustomerRepository.list_for_business(business_id)
        return [LoanBookService.get_customer_view(business_id, c.id) for c in customers]

    # --- Transaction history (bank-statement view) ---------------------

    @staticmethod
    def get_transaction_history(business_id: uuid.UUID) -> List[LoanHistoryEvent]:
        """Filtered to the same subset the frontend's Transaction
        History screen shows -- sales, payments, payment removals.
        Deletions/restores/receipt views still get recorded (for the
        eventual full audit trail) but don't belong on a screen whose
        entire premise is 'what money moved'."""
        from src.domains.business.loan_book.models.loan_history_event import TRANSACTION_EVENT_TYPES

        all_events = HistoryRepository.list_for_business(business_id)
        return [e for e in all_events if e.event_type in TRANSACTION_EVENT_TYPES]

    @staticmethod
    def get_full_history(business_id: uuid.UUID) -> List[LoanHistoryEvent]:
        """Every event, unfiltered -- for a future full-audit view."""
        return HistoryRepository.list_for_business(business_id)