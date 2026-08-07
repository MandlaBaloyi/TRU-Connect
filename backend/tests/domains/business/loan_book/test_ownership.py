"""
Ownership / IDOR (Insecure Direct Object Reference) tests.

THE MOST IMPORTANT TEST FILE IN THIS FEATURE. Loan Book is the first
resource in this whole backend that genuinely NEEDS per-owner isolation
-- Auth only ever had /me, which is inherently self-scoped and could
never actually test "can user A see user B's data" because there was
nothing to see. This is that test, now that a real second resource
exists.

Every test in this file follows the same shape: Business A creates real
data. Business B -- a completely separate, real business owner -- tries
to read, modify, or delete it using A's REAL id. Every attempt must fail
identically to how a non-existent id would fail (LoanBookNotFoundError,
never a different error, never a partial success) -- see
services/errors.py's docstring for why "not yours" and "doesn't exist"
must be indistinguishable to the caller.
"""
from __future__ import annotations

import pytest

from src.domains.business.loan_book.services.errors import LoanBookNotFoundError
from src.domains.business.loan_book.services.loan_book_service import LoanBookService
from src.shared.finance import Money


@pytest.fixture()
def business_a(make_business_user):
    return make_business_user("business-a@example.com")


@pytest.fixture()
def business_b(make_business_user):
    return make_business_user("business-b@example.com")


@pytest.fixture()
def business_a_customer(business_a):
    return LoanBookService.create_customer(business_a.id, "Mandla (A's customer)", "0783511969")


@pytest.fixture()
def business_a_entry(business_a, business_a_customer):
    return LoanBookService.create_entry(
        business_a.id, business_a_customer.id, Money(50000), description="A's private sale"
    )


class TestCustomerOwnership:
    def test_business_b_cannot_read_business_a_customer(self, business_b, business_a_customer):
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.get_customer(business_b.id, business_a_customer.id)

    def test_business_b_customer_list_never_includes_business_a_customers(
        self, business_b, business_a_customer
    ):
        """Not just 'direct fetch by ID fails' -- the LIST endpoint must
        never leak another business's rows either, which is a separate
        code path from get_by_id() and needs its own proof."""
        LoanBookService.create_customer(business_b.id, "Business B's own customer")

        b_customers = LoanBookService.list_customers(business_b.id)
        b_customer_ids = {c.id for c in b_customers}

        assert business_a_customer.id not in b_customer_ids

    def test_business_a_can_read_their_own_customer(self, business_a, business_a_customer):
        """The negative-case tests above are only meaningful alongside
        this: proving the legitimate owner is NOT accidentally blocked
        by whatever mechanism blocks everyone else."""
        found = LoanBookService.get_customer(business_a.id, business_a_customer.id)
        assert found.id == business_a_customer.id


class TestLoanEntryOwnership:
    def test_business_b_cannot_read_business_a_entry(self, business_b, business_a_entry):
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.get_entry(business_b.id, business_a_entry.id)

    def test_business_b_entry_list_never_includes_business_a_entries(
        self, business_a, business_a_entry, business_b
    ):
        entries = LoanBookService.list_entries(business_b.id)
        entry_ids = {v.entry.id for v in entries}
        assert business_a_entry.id not in entry_ids

    def test_business_b_cannot_pay_business_a_entry(self, business_b, business_a_entry):
        """The sharpest version of this test: B doesn't just try to
        READ A's entry, they try to record a REAL PAYMENT against it
        using A's real entry id. If this ever succeeded, business B
        could pay down -- or fraudulently mark settled -- a debt they
        have no relationship to at all."""
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.record_payment(business_b.id, business_a_entry.id, Money(10000))

    def test_business_b_cannot_delete_business_a_entry(self, business_b, business_a_entry):
        """Even more consequential than reading or paying: can B simply
        make A's real debt record disappear?"""
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.delete_entry(business_b.id, business_a_entry.id, reason="malicious")

    def test_business_b_cannot_create_an_entry_against_business_a_customer(
        self, business_b, business_a_customer
    ):
        """The reverse direction: B supplies A's REAL customer_id,
        trying to attach a new sale to a customer they don't own. This
        must fail exactly like the customer didn't exist, because from
        B's authorization perspective, it doesn't."""
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.create_entry(business_b.id, business_a_customer.id, Money(1000))

    def test_business_a_can_still_pay_and_delete_their_own_entry(
        self, business_a, business_a_entry
    ):
        """Same principle as the customer-ownership positive test: the
        isolation mechanism must not accidentally lock out the real
        owner."""
        view = LoanBookService.record_payment(business_a.id, business_a_entry.id, Money(10000))
        assert view.outstanding.minor_units == 40000

        LoanBookService.delete_entry(business_a.id, business_a_entry.id, reason="test cleanup")
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.get_entry(business_a.id, business_a_entry.id)


class TestNotFoundAndNotYoursAreIndistinguishable:
    """The precise property the whole authorization model rests on: an
    attacker probing IDs must get IDENTICAL responses whether they
    guessed a real ID belonging to someone else, or a random ID that
    was never real at all."""

    def test_genuinely_nonexistent_id_raises_the_same_exception(self, business_b):
        import uuid

        fake_id = uuid.uuid4()
        with pytest.raises(LoanBookNotFoundError):
            LoanBookService.get_customer(business_b.id, fake_id)

    def test_same_exception_type_for_both_cases(self, business_a, business_b, business_a_customer):
        """Directly compares the exception TYPE and MESSAGE for both
        scenarios -- they must be identical, not just both happen to be
        LoanBookNotFoundError with different text that could itself leak
        information."""
        import uuid

        errors = []
        for target_id in (business_a_customer.id, uuid.uuid4()):
            try:
                LoanBookService.get_customer(business_b.id, target_id)
            except LoanBookNotFoundError as exc:
                errors.append((type(exc), str(exc)))

        assert len(errors) == 2
        assert errors[0] == errors[1]
