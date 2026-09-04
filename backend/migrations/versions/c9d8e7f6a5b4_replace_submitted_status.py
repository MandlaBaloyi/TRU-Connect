"""replace stock_order SUBMITTED with real status model

Revision ID: c9d8e7f6a5b4
Revises: f6a2b8c4e9d1
Create Date: 2026-08-29 19:20:00.000000

Replaces the single, generic SUBMITTED status with a real model,
confirmed after direct review: PENDING_SUPPLIER_APPROVAL (where CASH
and PROOF_OF_PAYMENT land -- neither is verified in real time, so the
order genuinely isn't settled the moment it's placed), CONFIRMED
(where a real PayFast payment lands immediately, and where a pending
order moves once a supplier approves it), and DECLINED (a supplier
rejects the order). See stock_order.py's own StockOrderStatus
docstring for the full reasoning.

A FULL TYPE REBUILD, not ALTER TYPE ADD VALUE -- Postgres has no way
to remove an enum value without recreating the type, and leaving
SUBMITTED sitting in the enum as a dead, unreachable value would be
exactly the kind of loose end "production ready" means avoiding.

USES A TEMPORARY TEXT COLUMN, not a direct enum-to-enum USING cast --
real trial against the actual database showed Postgres's implicit
casting between two similarly-shaped-but-separately-named enum types
is genuinely fragile (multiple direct cast attempts failed with
"operator does not exist" even with explicit type qualification). A
plain text intermediate column, populated with a normal UPDATE
statement, sidesteps that ambiguity entirely -- more verbose, but
every step is a well-understood, unambiguous operation.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c9d8e7f6a5b4'
down_revision = 'f6a2b8c4e9d1'
branch_labels = None
depends_on = None

NEW_VALUES = ("CART", "AWAITING_PAYMENT", "PENDING_SUPPLIER_APPROVAL", "CONFIRMED", "DECLINED", "CANCELLED")
OLD_VALUES = ("CART", "AWAITING_PAYMENT", "SUBMITTED", "CANCELLED")


def upgrade():
    # 1. A plain text column holding the CURRENT status as a string --
    # no enum casting involved at all yet.
    op.execute("ALTER TABLE checkout.stock_orders ADD COLUMN status_text TEXT")
    op.execute("UPDATE checkout.stock_orders SET status_text = status::text")

    # 2. Drop the old enum column and its type entirely.
    op.execute("ALTER TABLE checkout.stock_orders DROP COLUMN status")
    op.execute("DROP TYPE checkout.stock_order_status")

    # 3. Remap the text values to their new meaning -- a normal
    # UPDATE, not a type cast.
    op.execute(
        "UPDATE checkout.stock_orders SET status_text = 'PENDING_SUPPLIER_APPROVAL' WHERE status_text = 'SUBMITTED'"
    )

    # 4. Create the new enum type, then convert the now-correct text
    # column into it -- a real, ordinary text-to-enum cast, not
    # enum-to-enum, which Postgres handles cleanly.
    new_enum = sa.Enum(*NEW_VALUES, name="stock_order_status", schema="checkout")
    new_enum.create(op.get_bind())
    op.execute(
        "ALTER TABLE checkout.stock_orders "
        "ALTER COLUMN status_text TYPE checkout.stock_order_status "
        "USING status_text::checkout.stock_order_status"
    )
    op.execute("ALTER TABLE checkout.stock_orders ALTER COLUMN status_text SET DEFAULT 'CART'")
    op.execute("ALTER TABLE checkout.stock_orders ALTER COLUMN status_text SET NOT NULL")
    op.execute("ALTER TABLE checkout.stock_orders RENAME COLUMN status_text TO status")


def downgrade():
    op.execute("ALTER TABLE checkout.stock_orders ADD COLUMN status_text TEXT")
    op.execute("UPDATE checkout.stock_orders SET status_text = status::text")
    op.execute("ALTER TABLE checkout.stock_orders DROP COLUMN status")
    op.execute("DROP TYPE checkout.stock_order_status")

    op.execute(
        "UPDATE checkout.stock_orders SET status_text = 'SUBMITTED' "
        "WHERE status_text IN ('PENDING_SUPPLIER_APPROVAL', 'CONFIRMED')"
    )
    op.execute("UPDATE checkout.stock_orders SET status_text = 'CANCELLED' WHERE status_text = 'DECLINED'")

    old_enum = sa.Enum(*OLD_VALUES, name="stock_order_status", schema="checkout")
    old_enum.create(op.get_bind())
    op.execute(
        "ALTER TABLE checkout.stock_orders "
        "ALTER COLUMN status_text TYPE checkout.stock_order_status "
        "USING status_text::checkout.stock_order_status"
    )
    op.execute("ALTER TABLE checkout.stock_orders ALTER COLUMN status_text SET DEFAULT 'CART'")
    op.execute("ALTER TABLE checkout.stock_orders ALTER COLUMN status_text SET NOT NULL")
    op.execute("ALTER TABLE checkout.stock_orders RENAME COLUMN status_text TO status")
