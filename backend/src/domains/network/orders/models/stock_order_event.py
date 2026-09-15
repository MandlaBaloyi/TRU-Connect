"""
StockOrderEvent -- an append-only log of everything that happens to a
marketplace order.

WHAT WAS MISSING (V2_13 §3.2). stock_orders carried only its CURRENT
status. "Why did this order change, and who changed it?" was
answerable by inference at best -- which is a support question that
already exists today, not a hypothetical.

Meanwhile the BUSINESS's own private books had this twice over
(LoanHistoryEvent, OrderHistoryEvent). The marketplace transaction --
the one where money moves between two parties who are not us -- had
none. This is the third use of a pattern this codebase already trusts,
not a new idea.

AND IT IS WHAT OUTBOUND WEBHOOKS WILL REPLAY FROM. A partner's ERP
needs order events pushed into it (V2_13 tier 4), and delivery
machinery replays from an event stream. Rows cannot be backfilled for
history that was never recorded, so the table has to exist BEFORE the
first partner, or their integration starts blind.

PLAIN db.Model, NOT BaseModel -- deliberately, and the same choice
OrderHistoryEvent made. BaseModel brings is_deleted/deleted_at, and a
history you can soft-delete is not a history. Append-only by
construction rather than by convention.

BOTH PARTIES ARE DENORMALISED ONTO THE ROW (business_id and
supplier_profile_id) so either side can read their own order history
without joining back through stock_orders, and so a webhook dispatcher
knows who to deliver to without a lookup. Same reasoning as
OrderHistoryEvent.business_id.

NOTHING CASCADES FROM HERE, and that is a decision rather than a
default (see docs/operations/BACKLOG.txt A4). A stock order that was
placed, confirmed and paid REALLY HAPPENED; deleting an account must
not erase the other party's record of a trade they were half of. When
account deletion is built, these rows are in the RETAIN group -- the
identifying columns get scrubbed, the transition history stays.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy.dialects.postgresql import UUID

from src.core.base_model import utcnow
from src.domains.network.orders.models.stock_order import StockOrderStatus
from src.extensions import db


class StockOrderEventType(str, enum.Enum):
    """WHAT happened, in the vocabulary a person would use.

    DELIBERATELY NOT JUST THE DESTINATION STATUS, even though
    to_status records that too. CANCELLED tells you the order ended;
    CANCELLED_BY_BUSINESS and CANCELLED_BY_SUPPLIER tell you which
    side walked away, which is the thing anybody actually asks. The
    status column cannot express that, because both produce the same
    status.
    """

    PLACED = "placed"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    CANCELLED_BY_BUSINESS = "cancelled_by_business"
    CANCELLED_BY_SUPPLIER = "cancelled_by_supplier"
    #: Declared ahead of the sweep that will write it -- an order the
    #: supplier never answered is a different story from one they
    #: actively refused, and support will be asked about both.
    AUTO_DECLINED = "auto_declined"
    #: The supplier says it left them. OPTIONAL -- most informal
    #: suppliers will never tap it, and its absence is not a gap.
    DISPATCHED = "dispatched"
    #: The business says it arrived. THE STRONG SIGNAL, and the only
    #: one a dispute can rest on.
    COMPLETED = "completed"
    #: Declared ahead of the sweep that will write it, exactly as
    #: AUTO_DECLINED was. An order nobody closed is a different story
    #: from one a shopkeeper confirmed receiving, and support will be
    #: asked about both. It means "nobody objected in time" and is not
    #: evidence that anything arrived.
    AUTO_COMPLETED = "auto_completed"
    #: Payment events, for when a real provider settles rather than a
    #: cash arrangement. Nothing writes these yet.
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"


class StockOrderEventActor(str, enum.Enum):
    BUSINESS = "business"
    SUPPLIER = "supplier"
    #: A scheduled job or a payment webhook -- nobody pressed anything.
    #: Its own value rather than a null actor, because "the system did
    #: it" and "we failed to record who did it" must not look alike.
    SYSTEM = "system"


class StockOrderEvent(db.Model):
    __tablename__ = "stock_order_events"
    __table_args__ = (
        db.Index("ix_stock_order_events_order", "stock_order_id", "occurred_at"),
        db.Index("ix_stock_order_events_business", "business_id", "occurred_at"),
        db.Index("ix_stock_order_events_supplier", "supplier_profile_id", "occurred_at"),
        {"schema": "checkout"},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    stock_order_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("checkout.stock_orders.id"), nullable=False
    )
    business_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=False)
    supplier_profile_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("supplier.supplier_profiles.id"), nullable=False
    )

    event_type = db.Column(
        db.Enum(StockOrderEventType, name="stock_order_event_type", schema="checkout"),
        nullable=False,
    )

    #: THE TRANSITION, NOT JUST THE DESTINATION. "Became cancelled from
    #: PENDING_SUPPLIER_APPROVAL" and "became cancelled from CONFIRMED"
    #: are different events commercially -- the second one cancels a
    #: trade the supplier had already agreed to. Recording only the new
    #: status would lose that distinction permanently.
    #:
    #: from_status is NULL exactly once per order, on PLACED, where
    #: there is no previous state worth naming.
    from_status = db.Column(
        db.Enum(StockOrderStatus, name="stock_order_status", schema="checkout", create_type=False),
        nullable=True,
    )
    to_status = db.Column(
        db.Enum(StockOrderStatus, name="stock_order_status", schema="checkout", create_type=False),
        nullable=False,
    )

    actor = db.Column(
        db.Enum(StockOrderEventActor, name="stock_order_event_actor", schema="checkout"),
        nullable=False,
    )
    #: NULL for SYSTEM events. Not null for anything a person did.
    actor_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("auth.users.id"), nullable=True)

    #: The supplier's decline reason, the business's cancellation
    #: reason, or a job's explanation. Free text, and the most useful
    #: column on the table when somebody is asking what went wrong.
    reason = db.Column(db.String(500), nullable=True)

    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "orderId": str(self.stock_order_id),
            "eventType": self.event_type.value,
            "fromStatus": self.from_status.value if self.from_status else None,
            "toStatus": self.to_status.value,
            "actor": self.actor.value,
            "actorUserId": str(self.actor_user_id) if self.actor_user_id else None,
            "reason": self.reason,
            "occurredAt": self.occurred_at.isoformat(),
        }
