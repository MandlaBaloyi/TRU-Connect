"""add order reference, buyer snapshot, supplier code

Revision ID: d5e6f7a8b9c0
Revises: c9d8e7f6a5b4
Create Date: 2026-08-31 15:20:00.000000

Real, human-facing identity for orders and suppliers, confirmed after
direct planning discussion. See stock_order.py and supplier_profile.py's
own column comments for the full reasoning on each field.

BACKFILLS EXISTING ROWS -- both supplier_code (every existing
supplier) and order_reference/submitted_at/buyer snapshot (every
existing order that's already past CART/AWAITING_PAYMENT). Done in
real Python, not raw SQL -- generating genuinely random, unique codes
per row isn't something worth reimplementing in SQL when the exact,
already-tested generator functions already exist. "Production ready"
means not leaving old rows sitting there with nulls a later query
could trip over, when backfilling them correctly is this
straightforward.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c9d8e7f6a5b4'
branch_labels = None
depends_on = None


def upgrade():
    # --- schema changes ---------------------------------------------------
    op.add_column("supplier_profiles", sa.Column("supplier_code", sa.String(length=4), nullable=True), schema="supplier")
    op.create_unique_constraint(
        "uq_supplier_profiles_supplier_code", "supplier_profiles", ["supplier_code"], schema="supplier"
    )

    op.add_column("stock_orders", sa.Column("order_reference", sa.String(length=20), nullable=True), schema="checkout")
    op.create_unique_constraint(
        "uq_stock_orders_order_reference", "stock_orders", ["order_reference"], schema="checkout"
    )
    op.add_column("stock_orders", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("buyer_name", sa.String(length=200), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("buyer_phone", sa.String(length=32), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("buyer_email", sa.String(length=255), nullable=True), schema="checkout")
    op.add_column("stock_orders", sa.Column("buyer_business_name", sa.String(length=255), nullable=True), schema="checkout")

    # --- backfill ------------------------------------------------------
    # REAL DEADLOCK FOUND AND FIXED: an earlier version of this
    # migration called generate_unique_supplier_code/
    # generate_unique_order_reference directly, which check uniqueness
    # via Flask-SQLAlchemy's own ORM session -- a SEPARATE connection
    # from this migration's own `connection` (op.get_bind()). That
    # session tried to query the same tables this transaction had
    # already locked (having just added columns to them), and hung
    # waiting on a lock this same transaction would never release
    # until that query finished. Confirmed genuinely reproduced by
    # running this against real "old-style" data before this fix --
    # local, connection-scoped generation and uniqueness checking
    # below avoids the second session entirely.
    import secrets

    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

    def _generate_unique_supplier_code(conn) -> str:
        for _ in range(10):
            code = "".join(secrets.choice(alphabet) for _ in range(4))
            exists = conn.execute(
                sa.text("SELECT 1 FROM supplier.supplier_profiles WHERE supplier_code = :code"), {"code": code}
            ).fetchone()
            if not exists:
                return code
        raise RuntimeError("Could not generate a unique supplier code during backfill.")

    def _generate_unique_order_reference(conn, supplier_code: str) -> str:
        for _ in range(10):
            suffix = "".join(secrets.choice(alphabet) for _ in range(6))
            reference = f"TRU-{supplier_code}-{suffix}"
            exists = conn.execute(
                sa.text("SELECT 1 FROM checkout.stock_orders WHERE order_reference = :ref"), {"ref": reference}
            ).fetchone()
            if not exists:
                return reference
        raise RuntimeError("Could not generate a unique order reference during backfill.")

    connection = op.get_bind()

    # Every existing supplier gets a real, unique code.
    supplier_rows = connection.execute(sa.text("SELECT id FROM supplier.supplier_profiles WHERE supplier_code IS NULL")).fetchall()
    supplier_code_by_profile_id = {}
    for (profile_id,) in supplier_rows:
        code = _generate_unique_supplier_code(connection)
        connection.execute(
            sa.text("UPDATE supplier.supplier_profiles SET supplier_code = :code WHERE id = :id"),
            {"code": code, "id": profile_id},
        )
        supplier_code_by_profile_id[str(profile_id)] = code

    # Every existing order that's genuinely past CART/AWAITING_PAYMENT
    # gets a real reference, a submitted_at (from its own updated_at,
    # the best available approximation for orders placed before this
    # column existed), and a buyer snapshot pulled from whatever's
    # currently on file for that business -- the best available
    # approximation for orders placed before snapshotting existed.
    order_rows = connection.execute(
        sa.text(
            """
            SELECT so.id, so.business_id, so.supplier_profile_id, so.updated_at
            FROM checkout.stock_orders so
            WHERE so.order_reference IS NULL
              AND so.status IN ('PENDING_SUPPLIER_APPROVAL', 'CONFIRMED', 'DECLINED')
            """
        )
    ).fetchall()

    for order_id, business_id, supplier_profile_id, updated_at in order_rows:
        supplier_code = supplier_code_by_profile_id.get(str(supplier_profile_id))
        if not supplier_code:
            # Row existed before this migration but its own supplier
            # row was somehow not touched above -- fetch it directly
            # rather than assume.
            result = connection.execute(
                sa.text("SELECT supplier_code FROM supplier.supplier_profiles WHERE id = :id"),
                {"id": supplier_profile_id},
            ).fetchone()
            supplier_code = result[0] if result else "XXXX"

        reference = _generate_unique_order_reference(connection, supplier_code)

        buyer_row = connection.execute(
            sa.text(
                """
                SELECT u.first_name, u.last_name, bp.phone, bp.email, bp.business_name
                FROM auth.users u
                LEFT JOIN business.business_profiles bp ON bp.business_id = u.id
                WHERE u.id = :business_id
                """
            ),
            {"business_id": business_id},
        ).fetchone()

        buyer_name = None
        buyer_phone = None
        buyer_email = None
        buyer_business_name = None
        if buyer_row:
            first_name, last_name, phone, email, business_name = buyer_row
            buyer_name = " ".join(part for part in [first_name, last_name] if part) or None
            buyer_phone = phone
            buyer_email = email
            buyer_business_name = business_name

        connection.execute(
            sa.text(
                """
                UPDATE checkout.stock_orders
                SET order_reference = :reference,
                    submitted_at = :submitted_at,
                    buyer_name = :buyer_name,
                    buyer_phone = :buyer_phone,
                    buyer_email = :buyer_email,
                    buyer_business_name = :buyer_business_name
                WHERE id = :id
                """
            ),
            {
                "reference": reference,
                "submitted_at": updated_at,
                "buyer_name": buyer_name,
                "buyer_phone": buyer_phone,
                "buyer_email": buyer_email,
                "buyer_business_name": buyer_business_name,
                "id": order_id,
            },
        )


def downgrade():
    op.drop_column("stock_orders", "buyer_business_name", schema="checkout")
    op.drop_column("stock_orders", "buyer_email", schema="checkout")
    op.drop_column("stock_orders", "buyer_phone", schema="checkout")
    op.drop_column("stock_orders", "buyer_name", schema="checkout")
    op.drop_column("stock_orders", "submitted_at", schema="checkout")
    op.drop_constraint("uq_stock_orders_order_reference", "stock_orders", schema="checkout", type_="unique")
    op.drop_column("stock_orders", "order_reference", schema="checkout")

    op.drop_constraint("uq_supplier_profiles_supplier_code", "supplier_profiles", schema="supplier", type_="unique")
    op.drop_column("supplier_profiles", "supplier_code", schema="supplier")
