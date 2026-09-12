"""An append-only event log for marketplace orders.

V2_13 §3.2. stock_orders carried only its CURRENT status, so "why did
this order change, and who changed it?" was answerable by inference at
best. The business's own private books already had this twice
(LoanHistoryEvent, OrderHistoryEvent); the marketplace transaction --
the one where money moves between two parties who are not us -- had
none.

It is also what outbound webhooks will replay from (tier 4). Rows
cannot be backfilled for history never recorded, which is why the
table lands before the first partner rather than with them.

REUSES checkout.stock_order_status rather than creating a parallel
type -- from_status/to_status must be comparable to stock_orders.status
or the log describes a different state machine from the one it logs.

NO CASCADES, deliberately (see docs/operations/BACKLOG.txt A4). A trade
that happened really happened; deleting an account must not erase the
other party's record of it. These rows are in the RETAIN group.

Revision ID: e6efcc9b331a
Revises: e0f4ed67d977
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e6efcc9b331a"
down_revision = "e0f4ed67d977"
branch_labels = None
depends_on = None

EVENT_TYPE = postgresql.ENUM(
    "PLACED", "CONFIRMED", "DECLINED", "CANCELLED_BY_BUSINESS",
    "CANCELLED_BY_SUPPLIER", "AUTO_DECLINED", "PAYMENT_RECEIVED", "PAYMENT_FAILED",
    name="stock_order_event_type", schema="checkout", create_type=False,
)
ACTOR = postgresql.ENUM(
    "BUSINESS", "SUPPLIER", "SYSTEM",
    name="stock_order_event_actor", schema="checkout", create_type=False,
)
# EXISTING type -- referenced, never created here.
ORDER_STATUS = postgresql.ENUM(
    name="stock_order_status", schema="checkout", create_type=False
)


def upgrade():
    bind = op.get_bind()
    EVENT_TYPE.create(bind, checkfirst=True)
    ACTOR.create(bind, checkfirst=True)

    op.create_table(
        "stock_order_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "stock_order_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("checkout.stock_orders.id"), nullable=False,
        ),
        sa.Column(
            "business_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id"), nullable=False,
        ),
        sa.Column(
            "supplier_profile_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("supplier.supplier_profiles.id"), nullable=False,
        ),
        sa.Column("event_type", EVENT_TYPE, nullable=False),
        sa.Column("from_status", ORDER_STATUS, nullable=True),
        sa.Column("to_status", ORDER_STATUS, nullable=False),
        sa.Column("actor", ACTOR, nullable=False),
        sa.Column(
            "actor_user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id"), nullable=True,
        ),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        schema="checkout",
    )

    op.create_index(
        "ix_stock_order_events_order", "stock_order_events",
        ["stock_order_id", "occurred_at"], schema="checkout",
    )
    op.create_index(
        "ix_stock_order_events_business", "stock_order_events",
        ["business_id", "occurred_at"], schema="checkout",
    )
    op.create_index(
        "ix_stock_order_events_supplier", "stock_order_events",
        ["supplier_profile_id", "occurred_at"], schema="checkout",
    )


def downgrade():
    op.drop_table("stock_order_events", schema="checkout")
    ACTOR.drop(op.get_bind(), checkfirst=True)
    EVENT_TYPE.drop(op.get_bind(), checkfirst=True)
