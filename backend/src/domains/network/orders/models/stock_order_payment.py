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
    """Deliberately minimal -- only what this pass actually reaches.
    CASH/PROOF_OF_PAYMENT go straight to SUCCEEDED the moment checkout
    completes (there's no verification step to wait on; a supplier
    confirming the money genuinely arrived is real, separate, later
    work on the supplier-side order-management feature). A real
    PayFast attempt would start at INITIATED and move to SUCCEEDED or
    FAILED only once the ITN webhook actually confirms it -- not
    reachable by anything in this pass, modelled now so wiring PayFast
    later doesn't need a migration just to add these two states."""

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
