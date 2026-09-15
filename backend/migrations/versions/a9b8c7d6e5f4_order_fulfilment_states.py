"""Let an order finish: DISPATCHED, COMPLETED, and who said so.

NOTHING EVER MOVED AN ORDER OUT OF CONFIRMED (V2_14 Part 1). A shop
placed an order, a supplier accepted it, stock changed hands in the
real world, and the record sat at CONFIRMED forever. "Open orders"
meant "every order ever accepted", and no dispute could rest on
anything because there was no moment the platform recognised as
finished.

TWO NEW STATUSES AND THREE COLUMNS:

    DISPATCHED      the supplier says it left them. OPTIONAL -- most
                    informal suppliers will never tap it, and an order
                    going straight from CONFIRMED to COMPLETED is the
                    ordinary path, not a degraded one.
    COMPLETED       finished, nothing further expected.
    completed_by    BUSINESS | SUPPLIER | SYSTEM.

completed_by IS THE POINT OF THE WHOLE MIGRATION. A SYSTEM completion
means "nobody objected in time" and is not evidence of anything; a
BUSINESS completion is a shopkeeper saying the stock is in their hands.
Collapsing those into one boolean would destroy the only distinction
that matters when somebody says it never arrived.

ADDING TO A POSTGRES ENUM IS NOT A COLUMN CHANGE. The two new statuses
are values on an existing type, so this uses ALTER TYPE ... ADD VALUE
rather than touching stock_orders at all -- and that is why the
downgrade cannot remove them: Postgres has no ADD VALUE inverse short
of rebuilding the type and rewriting every row that uses it. The
downgrade therefore reverses the COLUMNS and leaves the enum wider,
which is the honest half-measure rather than a rebuild that could lose
data.

NOTHING IS BACKFILLED. Every existing order is genuinely at whatever
status it holds; inventing a completion for historical trade would be
fabricating the exact evidence this migration exists to make
trustworthy.

A NOTE FOR ANYONE READING THE DEV DATABASE: stock_order_event_type
there also holds 'dispatched', 'completed' and 'auto_completed' in
lowercase. Those came from a first version of this file that added the
enum VALUES instead of the member NAMES, were caught before this was
pushed, and cannot be removed -- Postgres has no DROP VALUE. They are
unused and unreachable. A database that applies this migration for the
first time never gets them.

Revision ID: a9b8c7d6e5f4
Revises: c3d4e5f6a7b8
"""
from alembic import op
import sqlalchemy as sa


revision = "a9b8c7d6e5f4"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


COMPLETED_BY = sa.Enum(
    "BUSINESS",
    "SUPPLIER",
    "SYSTEM",
    name="stock_order_completed_by",
    schema="checkout",
)


def upgrade():
    bind = op.get_bind()

    # IF NOT EXISTS because ALTER TYPE ADD VALUE is not transactional in
    # older Postgres and a half-applied migration must be re-runnable.
    op.execute("ALTER TYPE checkout.stock_order_status ADD VALUE IF NOT EXISTS 'DISPATCHED'")
    op.execute("ALTER TYPE checkout.stock_order_status ADD VALUE IF NOT EXISTS 'COMPLETED'")

    # The event vocabulary follows the status. AUTO_COMPLETED is
    # declared ahead of the sweep that will write it, exactly as
    # AUTO_DECLINED was -- an order nobody closed is a different story
    # from one a shopkeeper confirmed, and support will be asked about
    # both.
    #
    # UPPERCASE, BECAUSE SQLALCHEMY PERSISTS THE MEMBER NAME, NOT ITS
    # VALUE. StockOrderEventType is one of the enums in this project
    # whose name and value differ (PLACED = "placed"), so the labels
    # already in the database are PLACED and AUTO_DECLINED. Adding
    # "dispatched" here would have created a value nothing can ever
    # write -- the exact mismatch ConnectionRequestStatus had to be
    # corrected for once already, caught here only because the two
    # cases sat next to each other in a \dT listing.
    for value in ("DISPATCHED", "COMPLETED", "AUTO_COMPLETED"):
        op.execute(
            f"ALTER TYPE checkout.stock_order_event_type ADD VALUE IF NOT EXISTS '{value}'"
        )

    COMPLETED_BY.create(bind, checkfirst=True)

    op.add_column(
        "stock_orders",
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        schema="checkout",
    )
    op.add_column(
        "stock_orders",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="checkout",
    )
    op.add_column(
        "stock_orders",
        sa.Column("completed_by", COMPLETED_BY, nullable=True),
        schema="checkout",
    )


def downgrade():
    op.drop_column("stock_orders", "completed_by", schema="checkout")
    op.drop_column("stock_orders", "completed_at", schema="checkout")
    op.drop_column("stock_orders", "dispatched_at", schema="checkout")

    bind = op.get_bind()
    COMPLETED_BY.drop(bind, checkfirst=True)

    # DISPATCHED and COMPLETED STAY ON THE STATUS ENUM. See the module
    # docstring: removing an enum value means rebuilding the type, and
    # any order already in one of those states would have nowhere to go.
    # A wider enum with no rows using it is harmless; a rebuild that
    # drops real orders is not.
