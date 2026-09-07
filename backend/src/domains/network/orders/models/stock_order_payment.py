"""
StockOrderPayment -- a payment ATTEMPT against a StockOrder, kept as
its own table rather than columns on stock_orders itself.

An order and a payment are genuinely different facts, not one fact
recorded twice: an order is the COMMERCIAL event ("this business wants
these products from this supplier"); a payment is the FINANCIAL event
("what actually happened when we tried to collect the money for it").
One order can have several payment attempts over its own lifetime --
a failed PayFast redirect, a retry that succeeds -- and collapsing
that history into the order's own row would silently lose exactly the
data real analytics, reconciliation, and support disputes need later.

NO PROVIDER-SPECIFIC COLUMNS ON stock_orders ITSELF -- deliberately.
An order stays "a TRU Connect order that may be paid through a
provider," never "a PayFast order." Every provider-specific detail
(their own transaction id, their own webhook payload) lives here
instead, one layer removed from the order -- the same isolation
principle already built into providers/, just applied to the schema.
"""
from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class StockOrderPaymentStatus(str, enum.Enum):
    """WHERE THE MONEY IS, not whether a call worked.

    THE BUG THIS ENUM WAS CHANGED TO FIX. CASH and PROOF_OF_PAYMENT
    used to be written SUCCEEDED the moment checkout completed, and
    that was a claim TRU Connect had no basis for. Cash is handed over
    on delivery, days later, by two people standing in a yard; nothing
    reaches this system at that moment. The row said money had moved
    when nothing had. It went unnoticed because only one query read it
    (the monthly spending cap), and for that one purpose the wrong
    value happened to give the right answer.

    THE DISTINCTION THAT FIXES IT is between two different facts that
    were being stored in one field:

      * an OBLIGATION -- "R1,000 is owed for this order". True from
        the moment the order is submitted, for every payment method,
        and TRU Connect can prove it because it created the order.
      * a SETTLEMENT -- "R1,000 actually changed hands". Only true
        when it actually happens, and for CASH/PROOF_OF_PAYMENT TRU
        Connect can never observe it directly at all.

    So:

      DUE       -- the obligation exists, nothing has been paid.
                   CASH and PROOF_OF_PAYMENT start here at checkout
                   and STAY here: nothing in the app records
                   settlement yet, so nothing may claim it.
      INITIATED -- a real gateway attempt is in flight, awaiting its
                   own webhook. PayFast only; not reachable yet.
      SUCCEEDED -- money genuinely changed hands. Now honest, because
                   nothing writes it at submission any more. Currently
                   unreachable, and that is correct rather than a gap:
                   the supplier-confirms-receipt action does not exist
                   yet, and PayFast is not wired.
      FAILED    -- a gateway attempt failed. PayFast only.

    HOW WE WOULD KNOW differs by method, and the difference is worth
    keeping in mind whenever this data is used to attest to anything.
    A PayFast SUCCEEDED is OBSERVED -- a gateway told us. A manual
    SUCCEEDED could only ever be DECLARED -- a person told us. Both
    are legitimate; they are not the same strength of evidence, and
    payment_method is what says which one you are looking at.

    NOTHING IS EVER DELETED FROM THIS TABLE. A payment that is never
    settled is a fact worth keeping, not litter to sweep up -- it is
    precisely the pattern an AML review would ask about.
    """

    DUE = "DUE"
    INITIATED = "INITIATED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class StockOrderPayment(BaseModel):
    __tablename__ = "stock_order_payments"
    __table_args__ = (
        db.Index("ix_stock_order_payments_stock_order_id", "stock_order_id"),
        {"schema": "checkout"},
    )

    stock_order_id = db.Column(UUID(as_uuid=True), db.ForeignKey("checkout.stock_orders.id"), nullable=False)
    # Mirrors StockOrder's own payment_method enum (same three values)
    # -- "provider" would have been a redundant second name for the
    # same thing at this stage; if TRU Connect ever adds a SECOND real
    # gateway alongside PayFast, that's a genuine reason to add a
    # distinct provider column then, not something to guess the shape
    # of now.
    payment_method = db.Column(
        db.Enum("CASH", "PROOF_OF_PAYMENT", "PAYFAST", name="stock_order_payment_method", schema="checkout"),
        nullable=False,
    )
    status = db.Column(
        db.Enum(StockOrderPaymentStatus, name="stock_order_payment_status", schema="checkout"),
        nullable=False,
        default=StockOrderPaymentStatus.INITIATED,
    )
    # Snapshotted from the order's own total_cents AT THE MOMENT of
    # this attempt -- same historical-snapshot principle already
    # applied to price_cents_at_add_time. A payment record should say
    # what THIS attempt was actually for, not silently drift if the
    # order it's attached to is ever touched again.
    amount_cents = db.Column(db.Integer, nullable=False)
    # 0 for CASH/PROOF_OF_PAYMENT always, computed via
    # commission.calculate_platform_commission_cents for PAYFAST --
    # the actual revenue-analytics field this whole table exists for.
    platform_commission_cents = db.Column(db.Integer, nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default="ZAR")
    # Nullable until a real gateway confirms one -- CASH/PROOF_OF_PAYMENT
    # never populate this at all; it stays null for the whole life of
    # those payment records.
    provider_transaction_id = db.Column(db.String(255), nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)
    # Raw, unprocessed webhook payload -- audit data, not something any
    # business logic should ever read back to make a decision.
    # Deliberately kept even after the payment's own status is decided,
    # for exactly the "months later, a dispute" scenario: being able to
    # show precisely what a provider actually sent, not a paraphrase
    # of it.
    raw_webhook_payload = db.Column(db.Text, nullable=True)
    initiated_at = db.Column(db.DateTime(timezone=True), nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
