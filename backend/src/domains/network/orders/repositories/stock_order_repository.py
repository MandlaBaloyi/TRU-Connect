"""
StockOrder repository -- ONLY talks to SQLAlchemy, no business rules,
same discipline as every other repository in this codebase.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from src.extensions import db
from src.domains.network.orders.models.stock_order import StockOrder, StockOrderItem, StockOrderStatus


class StockOrderRepository:
    @staticmethod
    def get_cart(business_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[StockOrder]:
        """Read-only -- no lock. Safe for ordinary "does a cart exist"
        checks (e.g. the badge count on Stock Catalogue) that don't
        need to mutate it."""
        return StockOrder.query.filter_by(
            business_id=business_id,
            supplier_profile_id=supplier_profile_id,
            status=StockOrderStatus.CART,
            is_deleted=False,
        ).first()

    @staticmethod
    def get_or_create_cart(business_id: str | UUID, supplier_profile_id: str | UUID) -> StockOrder:
        """THE REAL CONCURRENCY GUARANTEE this whole design exists
        for. Two near-simultaneous "Add to Cart" taps for the same
        (business, supplier) pair -- a genuine double-tap, or two
        devices signed into the same account -- must never both
        succeed in creating a separate CART row; that would silently
        split one business's own order into two, and the partial
        unique index (uq_stock_orders_one_cart_per_business_supplier)
        would reject the second INSERT outright rather than allow it.

        The sequence: try a locked SELECT first (the common case --
        the cart already exists, so lock it and return it, with no
        other concurrent caller able to read a stale version while
        this one is mutating it). Only INSERT when genuinely nothing
        exists yet. If a second, concurrent caller's own INSERT lands
        in the gap between this one's SELECT and INSERT (the real race
        this whole method exists to close), Postgres itself raises
        IntegrityError on the LOSING insert -- caught here, and
        resolved by re-running the locked SELECT, which will now
        correctly find the row the OTHER caller just created. Neither
        caller ever sees an error; both correctly converge on the
        exact same single row.
        """
        existing = (
            StockOrder.query.filter_by(
                business_id=business_id,
                supplier_profile_id=supplier_profile_id,
                status=StockOrderStatus.CART,
                is_deleted=False,
            )
            .with_for_update()
            .first()
        )
        if existing:
            return existing

        cart = StockOrder(business_id=business_id, supplier_profile_id=supplier_profile_id, status=StockOrderStatus.CART)
        db.session.add(cart)
        try:
            db.session.commit()
            return cart
        except IntegrityError:
            # A concurrent caller won the race and committed first --
            # this insert correctly failed against the partial unique
            # index. Roll back THIS failed attempt, then re-fetch: the
            # other caller's row now genuinely exists to find.
            db.session.rollback()
            existing = StockOrder.query.filter_by(
                business_id=business_id,
                supplier_profile_id=supplier_profile_id,
                status=StockOrderStatus.CART,
                is_deleted=False,
            ).first()
            if existing is None:
                # Practically unreachable (the IntegrityError itself
                # proves a CART row exists for this pair at the moment
                # it fired) -- but never silently return None from a
                # method whose whole contract is "always returns a
                # cart"; surface the real, unexpected state instead of
                # masking it.
                raise RuntimeError(
                    f"IntegrityError on cart creation for business={business_id}, "
                    f"supplier={supplier_profile_id}, but no existing CART row was found on retry."
                )
            return existing

    @staticmethod
    def list_carts_for_business(business_id: str | UUID) -> List[StockOrder]:
        """The Account tab's own "My Checkouts" hub -- every supplier
        this business currently has an incomplete cart with. Most
        recently updated first, matching "what did I touch most
        recently" being the most useful order for a list like this."""
        return (
            StockOrder.query.filter_by(business_id=business_id, status=StockOrderStatus.CART, is_deleted=False)
            .order_by(StockOrder.updated_at.desc())
            .all()
        )

    @staticmethod
    def list_submitted_for_business_and_supplier(
        business_id: str | UUID, supplier_profile_id: str | UUID
    ) -> List[StockOrder]:
        """"Order History" -- every order this business has actually
        SUBMITTED to this one supplier, most recent first. Scoped to a
        single supplier, matching the real request: a business viewing
        history from that supplier's own catalogue menu wants THEIR
        own order record with THAT supplier, not a mixed feed across
        every supplier they've ever ordered from."""
        return (
            StockOrder.query.filter_by(
                business_id=business_id,
                supplier_profile_id=supplier_profile_id,
                status=StockOrderStatus.SUBMITTED,
                is_deleted=False,
            )
            .order_by(StockOrder.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(stock_order_id: str | UUID) -> Optional[StockOrder]:
        return StockOrder.query.filter_by(id=stock_order_id, is_deleted=False).first()

    @staticmethod
    def get_item(stock_order_id: str | UUID, product_id: str | UUID) -> Optional[StockOrderItem]:
        return StockOrderItem.query.filter_by(
            stock_order_id=stock_order_id, product_id=product_id, is_deleted=False
        ).first()

    @staticmethod
    def add_or_increment_item(stock_order_id: str | UUID, product_id: str | UUID, quantity: int, price_cents: int):
        """A given product can only ever have ONE row per cart -- see
        the model's own uq_stock_order_items_order_product index.
        Adding a product already in the cart increments its existing
        quantity rather than creating a second row; price_cents_at_add_time
        is only ever set on FIRST add and never touched again, matching
        this whole design's own "captured once" guarantee."""
        existing = StockOrderRepository.get_item(stock_order_id, product_id)
        if existing:
            existing.quantity += quantity
            db.session.commit()
            return existing

        item = StockOrderItem(
            stock_order_id=stock_order_id, product_id=product_id, quantity=quantity, price_cents_at_add_time=price_cents
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def set_item_quantity(item: StockOrderItem, quantity: int) -> StockOrderItem:
        item.quantity = quantity
        db.session.commit()
        return item

    @staticmethod
    def delete_item(item: StockOrderItem) -> None:
        db.session.delete(item)
        db.session.commit()

    @staticmethod
    def delete_all_items(stock_order_id: str | UUID) -> None:
        """"Clear Cart" -- a real batch delete, not a loop of
        individual delete_item calls from the service layer. One
        query, one commit, rather than N round-trips for a cart with
        N items."""
        StockOrderItem.query.filter_by(stock_order_id=stock_order_id).delete()
        db.session.commit()

    @staticmethod
    def recalculate_total(stock_order_id: str | UUID) -> int:
        """A real, fresh SUM query against the database -- never
        trusted from an in-memory relationship that could be stale
        after a sibling operation. Returns the new total; callers
        write it onto the StockOrder themselves so this method stays a
        pure read."""
        total = (
            db.session.query(db.func.coalesce(db.func.sum(StockOrderItem.quantity * StockOrderItem.price_cents_at_add_time), 0))
            .filter(StockOrderItem.stock_order_id == stock_order_id, StockOrderItem.is_deleted.is_(False))
            .scalar()
        )
        return int(total)

    @staticmethod
    def save_total(stock_order: StockOrder, total_cents: int) -> StockOrder:
        stock_order.total_cents = total_cents
        db.session.commit()
        return stock_order
