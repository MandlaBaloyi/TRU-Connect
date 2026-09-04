"""
shared/checkout -- the real, persistent cart-and-order lifecycle for a
business ordering from a supplier. Lives in shared/, not inside either
business/ or supplier/, for the same reason shared/media does: both
roles genuinely need this (a business builds and submits a cart; a
supplier will later need to see and act on what's submitted), and it
doesn't belong to either side alone.

ONE ROW, ONE LIFECYCLE -- same discipline as ConnectionRequest: a
StockOrder is a CART while being built and the SAME row becomes the
SUBMITTED order once checkout completes. Never two separate tables
with a copy step between them; a copy step is exactly where a real
mistake (a price silently drifting between "cart" and "order", an item
lost in translation) would happen.

WHY THIS SCHEMA IS "checkout", NOT tucked inside network/connections or
supplier/products: this is genuinely new infrastructure with its own
concerns (money, quantities, delivery, payment provider integration)
that neither of those domains owns, and it needs its own dedicated
Postgres schema for the same reason shared/media has its own "media"
schema rather than living in "supplier" or "business" -- ownership
should be visible in the schema name itself, not implied.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import BaseModel
from src.extensions import db


class StockOrderStatus(str, enum.Enum):
    """CART -- being built, freely editable (add/update/remove items),
    never shown to a supplier.

    AWAITING_PAYMENT -- reserved, not reachable by anything in this
    pass. A real digital payment (PayFast) genuinely needs an
    intermediate state: the business is redirected to PayFast, pays,
    then returns -- the order isn't confirmed until that payment
    actually succeeds. CASH and PROOF_OF_PAYMENT skip this entirely.

    PENDING_SUPPLIER_APPROVAL -- REPLACES the old, single SUBMITTED
    state, for CASH and PROOF_OF_PAYMENT specifically. Confirmed
    directly after review: neither method is verified in real time,
    so the order genuinely isn't settled the moment it's placed --
    it's waiting on the supplier's own decision (approve/decline, a
    separate, later feature). A business should see that real,
    honest state, not a generic "submitted" that implies more
    certainty than actually exists yet.

    CONFIRMED -- where a real PAYFAST payment lands immediately (a
    verified gateway payment needs no supplier approval at all -- the
    fraud/reliability concern PENDING_SUPPLIER_APPROVAL exists for
    doesn't apply to it), and where a PENDING_SUPPLIER_APPROVAL order
    moves once the supplier actually approves it. Not reachable by
    anything in this pass -- the approve action itself is real,
    separate, later supplier-side work -- modelled now so that
    feature lands as an additive change, not a status-model rework.

    DECLINED -- a supplier rejects a PENDING_SUPPLIER_APPROVAL order.
    Not reachable by anything in this pass, same reasoning as
    CONFIRMED above.

    CANCELLED -- reserved, not reachable by anything in this pass.
    Either side cancelling before fulfilment is real, future work.
    """

    CART = "CART"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    PENDING_SUPPLIER_APPROVAL = "PENDING_SUPPLIER_APPROVAL"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"


class StockOrderDeclineReason(str, enum.Enum):
    """A supplier's own reason for declining a PENDING_SUPPLIER_APPROVAL
    order. Mirrors SupplierReportReason exactly -- same "preset
    reasons plus a genuine free-text escape hatch" shape, deliberately
    reused rather than invented separately."""

    OUT_OF_STOCK = "out_of_stock"
    CANNOT_FULFIL_DELIVERY_AREA = "cannot_fulfil_delivery_area"
    PRICING_ERROR = "pricing_error"
    SUSPECTED_FRAUD = "suspected_fraud"
    # NOT chosen by a supplier -- set only by
    # stock_order_auto_decline_sweep_job.py when an order sat
    # unanswered past the real, final timeout. Kept as a genuine enum
    # member (not a bare string) so it's validated and displayed the
    # exact same way as every other reason, and so the frontend's own
    # DECLINE_REASON_LABELS can show it honestly rather than falling
    # back to a raw, ugly enum value.
    NO_RESPONSE = "no_response"
    OTHER = "other"


class StockOrderPaymentMethod(str, enum.Enum):
    """Null on a CART -- a business hasn't chosen how they're paying
    until they actually check out. Set exactly once, at submission."""

    CASH = "CASH"
    PROOF_OF_PAYMENT = "PROOF_OF_PAYMENT"
    PAYFAST = "PAYFAST"  # not reachable by anything in this pass -- see providers/payfast_provider.py


class StockOrderDeliveryType(str, enum.Enum):
    DELIVER = "DELIVER"
    COLLECT = "COLLECT"


class StockOrder(BaseModel):
    __tablename__ = "stock_orders"
    __table_args__ = (
        db.Index("ix_stock_orders_business_id", "business_id"),
        db.Index("ix_stock_orders_supplier_profile_id", "supplier_profile_id"),
        # THE REAL "unique, connecting to a specific supplier"
        # GUARANTEE -- a partial unique index, not a plain one: only
        # ONE row with status='CART' can exist per (business,
        # supplier) pair at any time, enforced by Postgres itself, not
        # just application code that could be bypassed by a second
        # concurrent request. A business CAN have many SUBMITTED
        # orders over time with the same supplier -- this constraint
        # only ever applies to the single, currently-being-built cart.
        db.Index(
            "uq_stock_orders_one_cart_per_business_supplier",
            "business_id",
            "supplier_profile_id",
            unique=True,
            postgresql_where=db.text("status = 'CART'"),
        ),
        {"schema": "checkout"},
    )

    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )
    status = db.Column(
        db.Enum(StockOrderStatus, name="stock_order_status", schema="checkout"),
        nullable=False,
        default=StockOrderStatus.CART,
    )
    payment_method = db.Column(
        db.Enum(StockOrderPaymentMethod, name="stock_order_payment_method", schema="checkout"), nullable=True
    )
    delivery_type = db.Column(
        db.Enum(StockOrderDeliveryType, name="stock_order_delivery_type", schema="checkout"), nullable=True
    )
    # Free-text snapshot of the delivery address at submission time --
    # deliberately NOT a foreign key to some future "saved addresses"
    # table. An address that's correct today and edited or deleted
    # next month must never silently rewrite what a past order says it
    # was delivered to; a real order's own delivery details are a
    # historical fact, not a live reference.
    delivery_address_text = db.Column(db.Text, nullable=True)
    # Cached, not computed on every read -- same reasoning as any
    # denormalised total: recalculating from every line item on every
    # list-view render doesn't scale once a business has many
    # historical orders. Recomputed and re-written by cart_service
    # every time an item is added/updated/removed, so it's never
    # allowed to drift from the real sum of its own items.
    total_cents = db.Column(db.Integer, nullable=False, default=0)

    # The real, human-facing order reference -- TRU-{supplier_code}-
    # {6 chars}, see algorithms/order_reference_generator.py for the
    # full reasoning. Assigned ONLY at submission, never at cart
    # creation -- an abandoned cart should never consume one. Nullable
    # at the schema level for exactly that reason: every CART row
    # genuinely has none yet, this isn't a migration-backfill gap.
    order_reference = db.Column(db.String(20), nullable=True, unique=True)

    # A REAL, DEDICATED timestamp -- deliberately NOT reusing
    # updated_at for this. A found-and-fixed latent bug: updated_at
    # will also change the moment a future supplier-side approve/
    # decline touches this same row, which would have silently
    # shifted what "submitted at" appeared to mean. This column is
    # set exactly once, at the real moment of submission, and never
    # touched again.
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Buyer details, SNAPSHOTTED at submission -- same historical-fact
    # reasoning as delivery_address_text and price_cents_at_add_time
    # above: if a business updates their phone number next month, a
    # supplier looking back at an old order should see what was true
    # when it was actually placed, not a silently-changed current
    # value pulled from a live join.
    buyer_name = db.Column(db.String(200), nullable=True)
    buyer_phone = db.Column(db.String(32), nullable=True)
    buyer_email = db.Column(db.String(255), nullable=True)
    buyer_business_name = db.Column(db.String(255), nullable=True)

    # A supplier's own decision on a PENDING_SUPPLIER_APPROVAL order --
    # nullable, since most orders never reach DECLINED at all.
    # Structured reason + optional free-text details, mirroring
    # SupplierReportReason/SupplierReport.details exactly (same
    # "preset reasons plus a genuine free-text escape hatch" shape,
    # not invented separately) -- a real supplier decision deserves
    # the same discipline as a real report.
    decline_reason = db.Column(db.String(50), nullable=True)
    decline_details = db.Column(db.String(1000), nullable=True)

    # Reminder tracking -- nullable, set once each reminder actually
    # sends. Two separate columns, not one, since the 24h and 3-day
    # reminders are genuinely two different real events a supplier
    # receives -- a single "reminded" boolean couldn't tell
    # stock_order_reminder_sweep_job.py which one still needs sending
    # without re-sending the other. NULL on both is the normal state
    # for the vast majority of orders, which get decided long before
    # either threshold is ever reached.
    first_reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    second_reminder_sent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    items = db.relationship("StockOrderItem", backref="stock_order", lazy="selectin", cascade="all, delete-orphan")


class StockOrderItem(BaseModel):
    __tablename__ = "stock_order_items"
    __table_args__ = (
        db.Index("ix_stock_order_items_stock_order_id", "stock_order_id"),
        # A given product can only appear ONCE per cart -- adding the
        # same product twice increases ITS quantity, never creates a
        # second, separate row for it. Enforced here, not just in
        # cart_service, for the same "the database is the real
        # guarantee, application code alone can be raced" reasoning as
        # the one-cart-per-supplier index above.
        db.Index("uq_stock_order_items_order_product", "stock_order_id", "product_id", unique=True),
        {"schema": "checkout"},
    )

    stock_order_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("checkout.stock_orders.id"), nullable=False
    )
    # NOT ondelete=CASCADE -- deliberately. A product referenced by a
    # real cart/order item can never be hard-deleted while that
    # reference exists; every deletion in this codebase is already
    # soft (is_deleted=True), so this FK simply can't be violated by
    # normal product-management flows. See cart_service's own
    # docstring for how a since-archived or since-deleted product is
    # actually handled at checkout time (rejected with a clear error,
    # never silently let through).
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey("supplier.products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # THE REAL PRICE-DRIFT PROTECTION -- captured once, at the moment
    # this item is added, and never re-read from the live Product row
    # again. A supplier changing a price after a business has already
    # added the item to their cart must never silently change what
    # that business sees they're about to pay; a genuine price change
    # is a NEW decision for the business to see and accept, not a
    # retroactive edit to something already in their cart.
    price_cents_at_add_time = db.Column(db.Integer, nullable=False)
