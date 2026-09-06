"""
StockOrder repository -- ONLY talks to SQLAlchemy, no business rules,
same discipline as every other repository in this codebase.
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
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
        placed with this one supplier, most recent first. Scoped to a
        single supplier, matching the real request: a business viewing
        history from that supplier's own catalogue menu wants THEIR
        own order record with THAT supplier, not a mixed feed across
        every supplier they've ever ordered from.

        "Placed" means PENDING_SUPPLIER_APPROVAL, CONFIRMED, or
        DECLINED -- any status reachable only by genuinely completing
        checkout, never CART (still being built) or AWAITING_PAYMENT
        (a real gateway attempt still in progress, not yet a real
        order)."""
        return (
            StockOrder.query.filter_by(
                business_id=business_id,
                supplier_profile_id=supplier_profile_id,
                is_deleted=False,
            )
            .filter(
                StockOrder.status.in_(
                    [StockOrderStatus.PENDING_SUPPLIER_APPROVAL, StockOrderStatus.CONFIRMED, StockOrderStatus.DECLINED]
                )
            )
            .order_by(StockOrder.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(stock_order_id: str | UUID) -> Optional[StockOrder]:
        return StockOrder.query.filter_by(id=stock_order_id, is_deleted=False).first()

    @staticmethod
    def get_by_id_for_business_and_supplier(
        stock_order_id: str | UUID, business_id: str | UUID, supplier_profile_id: str | UUID
    ) -> Optional[StockOrder]:
        """The real "Order History" detail lookup -- deliberately
        scoped by BOTH business_id and supplier_profile_id, not just
        the order's own id. get_by_id above has no such scoping and
        must never be used for anything business-facing; a business
        guessing or otherwise obtaining another business's own order
        id must never be able to view its contents. Same IDOR-safety
        shape as every other domain's own get_by_id_and_<owner>
        repository method."""
        return StockOrder.query.filter_by(
            id=stock_order_id, business_id=business_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def get_by_id_for_supplier(stock_order_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[StockOrder]:
        """The supplier-side mirror of get_by_id_for_business_and_supplier
        -- same IDOR-safety shape, just scoped from the other
        direction: a supplier must never be able to view or act on an
        order that belongs to a different supplier, even with a
        genuinely valid order id."""
        return StockOrder.query.filter_by(
            id=stock_order_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def list_pending_for_supplier(supplier_profile_id: str | UUID) -> List[StockOrder]:
        """A supplier's own real "incoming orders" queue -- every
        PENDING_SUPPLIER_APPROVAL order waiting on their decision,
        most recently submitted first (oldest-waiting-last would bury
        a supplier's most urgent, newest order under a long list of
        already-seen ones)."""
        return (
            StockOrder.query.filter_by(
                supplier_profile_id=supplier_profile_id,
                status=StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
                is_deleted=False,
            )
            .order_by(StockOrder.submitted_at.desc())
            .all()
        )

    @staticmethod
    def list_by_status_for_supplier(
        supplier_profile_id: str | UUID,
        status: StockOrderStatus,
        submitted_from: Optional[datetime] = None,
        submitted_to: Optional[datetime] = None,
    ) -> List[StockOrder]:
        """The Approved/Declined tabs' own real query -- a supplier's
        full history for one specific status, optionally narrowed to
        a real date range. Deliberately a SEPARATE method from
        list_pending_for_supplier above rather than one, more heavily
        parameterized function: "New" has no date filter at all (it's
        inherently "right now"), so forcing every caller through one
        shared signature would mean list_pending_for_supplier's own
        callers carrying two always-None parameters they never use."""
        query = StockOrder.query.filter_by(
            supplier_profile_id=supplier_profile_id, status=status, is_deleted=False
        )
        if submitted_from is not None:
            query = query.filter(StockOrder.submitted_at >= submitted_from)
        if submitted_to is not None:
            query = query.filter(StockOrder.submitted_at <= submitted_to)
        return query.order_by(StockOrder.submitted_at.desc()).all()

    @staticmethod
    def list_awaiting_first_reminder(older_than: datetime) -> List[StockOrder]:
        """stock_order_reminder_sweep_job's own 24h query -- every
        still-pending order submitted before the given cutoff that
        has never been reminded about at all."""
        return StockOrder.query.filter(
            StockOrder.status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
            StockOrder.is_deleted == False,  # noqa: E712 -- SQLAlchemy requires == here, not `is`
            StockOrder.submitted_at <= older_than,
            StockOrder.first_reminder_sent_at.is_(None),
        ).all()

    @staticmethod
    def list_awaiting_second_reminder(older_than: datetime) -> List[StockOrder]:
        """stock_order_reminder_sweep_job's own 3-day query -- every
        still-pending order that already got its first reminder, past
        the given cutoff, that hasn't had its second one yet."""
        return StockOrder.query.filter(
            StockOrder.status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
            StockOrder.is_deleted == False,  # noqa: E712
            StockOrder.submitted_at <= older_than,
            StockOrder.first_reminder_sent_at.isnot(None),
            StockOrder.second_reminder_sent_at.is_(None),
        ).all()

    @staticmethod
    def list_awaiting_auto_decline(older_than: datetime) -> List[StockOrder]:
        """stock_order_auto_decline_sweep_job's own final-timeout
        query -- every still-pending order submitted before the given
        cutoff, regardless of reminder state (an order that somehow
        never got reminded still needs to be resolved, not left
        pending forever just because the reminder step itself failed
        or was skipped)."""
        return StockOrder.query.filter(
            StockOrder.status == StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
            StockOrder.is_deleted == False,  # noqa: E712
            StockOrder.submitted_at <= older_than,
        ).all()

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

    @staticmethod
    def reliability_stats_for_supplier(supplier_profile_id: str | UUID) -> dict:
        """Real fulfilment history for a supplier's brand profile:
        how many decided orders they've had, how many they accepted,
        and how long they typically took to decide.

        DECIDED ORDERS ONLY -- an order still sitting in
        PENDING_SUPPLIER_APPROVAL hasn't been accepted OR refused yet,
        so counting it either way would be a guess. CANCELLED is
        excluded too: a business cancelling their own order says
        nothing about the supplier.

        MEDIAN, not mean, for the response time -- one supplier who
        went on holiday for three weeks once shouldn't define what
        "usually" means for them.

        Returns raw numbers only. Whether there's ENOUGH history to
        show any of this to a business is a judgement the service makes
        (see showcase-side MIN_ORDERS_FOR_RELIABILITY), not something a
        repository should decide.
        """
        from src.domains.network.orders.models.stock_order import StockOrder, StockOrderStatus

        decided = (
            StockOrder.query.filter(
                StockOrder.supplier_profile_id == supplier_profile_id,
                StockOrder.is_deleted.is_(False),
                StockOrder.decided_at.isnot(None),
                StockOrder.status.in_([StockOrderStatus.CONFIRMED, StockOrderStatus.DECLINED]),
            )
            .with_entities(StockOrder.status, StockOrder.submitted_at, StockOrder.decided_at)
            .all()
        )

        if not decided:
            return {"decidedCount": 0, "acceptedCount": 0, "medianResponseHours": None}

        accepted = sum(1 for row in decided if row.status == StockOrderStatus.CONFIRMED)

        durations = [
            (row.decided_at - row.submitted_at).total_seconds() / 3600
            for row in decided
            if row.submitted_at is not None and row.decided_at is not None
        ]
        median_hours = None
        if durations:
            durations.sort()
            middle = len(durations) // 2
            median_hours = (
                durations[middle]
                if len(durations) % 2
                else (durations[middle - 1] + durations[middle]) / 2
            )

        return {
            "decidedCount": len(decided),
            "acceptedCount": accepted,
            "medianResponseHours": median_hours,
        }
