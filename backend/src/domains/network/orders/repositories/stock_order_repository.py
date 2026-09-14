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
    def trust_stats_for_supplier(supplier_profile_id: str | UUID) -> dict:
        """A supplier's real trading record: how many orders they've
        accepted, and how many businesses have come back to order again.

        THESE ARE LIVE COUNTS OF CURRENT STATE, not a running tally.
        Every call re-counts rows whose status is CONFIRMED right now,
        so the figures grow as a supplier accepts more work -- but they
        also DROP if a supplier cancels an order they had already
        confirmed (order_management_service's CONFIRMED -> CANCELLED).
        That is the correct behaviour, not a leak: an order the supplier
        pulled out of is not one they fulfilled, and a business reading
        "112 orders accepted" should not be counting orders that were
        taken back. It does mean the number is not monotonic, which an
        earlier version of this docstring wrongly claimed.

        WHY COUNTS AND NOT RATES -- this replaced an "accepted X of
        their last Y" ratio plus a median response time, and both were
        removed for the same underlying reason: a supplier could do
        everything right and watch the number not move, or get worse.

          * The ratio led with the failures. A new supplier's first
            decline read as "accepted 0 of 1" -- a damning headline
            earned by one order.
          * The median response time actively ignored improvement. It
            is designed to resist outliers, so a supplier with a slow
            history who answers the next order in minutes sees no
            change at all. Reported directly: "I just approved an order
            but it's not changing." Correct statistics, useless
            feedback.

        A count of accepted orders moves the moment a supplier accepts
        something, and is the number a business actually wants ("have
        these people done this before, and how often"). ALL-TIME,
        deliberately not a recent window: a long trading history is
        exactly the thing worth showing, and unlike a rate it can't be
        dragged down by age.

        REPEAT BUYERS WAS HERE AND IS NOT ANY MORE. It is still the
        strongest signal in this data -- a business coming back a
        second time is a verdict on the first order that no
        self-reported claim can imitate -- but strength was never the
        question. It says something about how the supplier PERFORMS,
        not about their standing with strangers, and acting on it is
        the supplier's own business rather than a stranger's. It now
        lives in performance_stats_for_supplier below, with the other
        figures a supplier can actually do something about.

        UNITS SOLD LEFT FOR THE SAME REASON, with one of its own: it
        was in this payload but no business-facing screen ever rendered
        it, so it was being handed to businesses purely by accident of
        history. It is a second view of "orders accepted" rather than a
        separate question, and it stayed in
        performance_stats_for_supplier where volume is actionable.

        THIS PAYLOAD IS DELIBERATELY DOWN TO ONE KEY, and that is the
        point rather than an oversight. What a business sees is exactly
        three things: how many businesses are connected (counted
        elsewhere, it is a connection fact not an order fact), how many
        orders this supplier accepted, and -- once it can be measured
        at all -- how many were fulfilled. Nothing else from this
        domain reaches a business-facing payload.

        That is what lets the supplier's own Settings screen list the
        public set in three lines and be telling the literal truth. If
        a fourth figure is ever added here, that screen is wrong the
        same day, so add it there too.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        accepted = StockOrder.query.filter(
            StockOrder.supplier_profile_id == supplier_profile_id,
            StockOrder.is_deleted.is_(False),
            StockOrder.status == StockOrderStatus.CONFIRMED,
        )

        return {
            "acceptedOrderCount": accepted.count(),
        }

    @staticmethod
    def previously_ordered_product_ids(
        business_id: str | UUID, supplier_profile_id: str | UUID, limit: int = 12
    ) -> List[UUID]:
        """Products THIS business has previously had accepted by THIS
        supplier, most recently ordered first.

        The single most useful query in an informal-wholesale app: a
        spaza owner restocking buys the same handful of things every
        week, and today they have to re-find each one by scrolling a
        category. Ordering is per-BUSINESS, so this is genuinely
        personal history rather than a popularity list dressed up as
        one.

        CONFIRMED ONLY. A cart nobody checked out, or an order the
        supplier declined, is not something the business "ordered" --
        offering to reorder either would be offering to repeat
        something that never happened.

        Returns IDs, not products: the caller already has the enrichment
        pipeline (build_catalog_product_dicts) and needs the products
        loaded the same way as every other catalogue read, not a second
        slightly-different shape.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        rows = (
            db.session.query(
                StockOrderItem.product_id,
                db.func.max(StockOrder.submitted_at).label("last_ordered"),
            )
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrder.business_id == business_id,
                StockOrder.supplier_profile_id == supplier_profile_id,
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
            .group_by(StockOrderItem.product_id)
            .order_by(db.text("last_ordered DESC NULLS LAST"))
            .limit(limit)
            .all()
        )
        return [row.product_id for row in rows]

    @staticmethod
    def buyer_count_for_product(product_id: str | UUID) -> int:
        """How many DISTINCT businesses have had an order accepted that
        included this product.

        The one question a shop owner asks that a spec sheet can't
        answer: "will this actually sell". Another business putting
        money on it is the closest thing to an answer available before
        you've stocked it yourself.

        DISTINCT BUSINESSES, not order count and not units: one buyer
        ordering weekly is a loyal customer, not fifty endorsements, and
        counting orders would let a single business inflate a product
        indefinitely.

        CONFIRMED only -- a declined order or an abandoned cart is not
        somebody buying something.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        return (
            db.session.query(StockOrder.business_id)
            .join(StockOrderItem, StockOrderItem.stock_order_id == StockOrder.id)
            .filter(
                StockOrderItem.product_id == product_id,
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
            .distinct()
            .count()
        )

    @staticmethod
    def performance_stats_for_supplier(supplier_profile_id: str | UUID, window: int = 20) -> dict:
        """The supplier's OWN performance figures -- deliberately a
        different set from trust_stats_for_supplier above.

        WHY TWO SETS AND NOT ONE WITH A VISIBILITY FLAG. These two
        audiences need opposite things from the same data:

          * A BUSINESS needs signals that are hard to fake and fair to a
            newcomer, so the public set is counts that only grow and
            hide at zero. Nothing there can make a supplier look bad.
          * A SUPPLIER needs signals that tell them what to FIX.
            Acceptance rate and reply time are exactly that -- and
            they're exactly what was removed from the public profile,
            because publicly they punish one bad week ("accepted 0 of
            1") while privately they're the most actionable numbers a
            supplier has.

        Same rows in the database, opposite purposes on screen. Folding
        them into one set behind a flag would have meant showing a
        business a number designed to be self-criticism.

        `window` bounds the acceptance/reply figures to recent history,
        so a supplier who has improved can actually see it move -- the
        all-time versions would be dragged by orders from a year ago.
        """
        from datetime import timedelta

        from src.core.base_model import utcnow
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        decided = (
            StockOrder.query.filter(
                StockOrder.supplier_profile_id == supplier_profile_id,
                StockOrder.is_deleted.is_(False),
                StockOrder.decided_at.isnot(None),
                StockOrder.status.in_([StockOrderStatus.CONFIRMED, StockOrderStatus.DECLINED]),
            )
            .with_entities(StockOrder.status, StockOrder.submitted_at, StockOrder.decided_at)
            .order_by(StockOrder.decided_at.desc())
            .limit(window)
            .all()
        )
        accepted_recent = sum(1 for row in decided if row.status == StockOrderStatus.CONFIRMED)

        durations = sorted(
            (row.decided_at - row.submitted_at).total_seconds() / 3600
            for row in decided
            if row.submitted_at is not None and row.decided_at is not None
        )
        median_hours = None
        if durations:
            middle = len(durations) // 2
            median_hours = (
                durations[middle]
                if len(durations) % 2
                else (durations[middle - 1] + durations[middle]) / 2
            )

        confirmed = StockOrder.query.filter(
            StockOrder.supplier_profile_id == supplier_profile_id,
            StockOrder.is_deleted.is_(False),
            StockOrder.status == StockOrderStatus.CONFIRMED,
        )

        sales_cents = (
            db.session.query(db.func.coalesce(db.func.sum(StockOrder.total_cents), 0))
            .filter(
                StockOrder.supplier_profile_id == supplier_profile_id,
                StockOrder.is_deleted.is_(False),
                StockOrder.status == StockOrderStatus.CONFIRMED,
            )
            .scalar()
        )

        units = (
            db.session.query(db.func.coalesce(db.func.sum(StockOrderItem.quantity), 0))
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrder.supplier_profile_id == supplier_profile_id,
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
            .scalar()
        )

        # CANCELLED BY THE SUPPLIER specifically -- an order the
        # BUSINESS pulled out of says nothing about the supplier, and
        # counting it here would be blaming them for someone else's
        # change of mind.
        cancelled_after_confirming = StockOrder.query.filter(
            StockOrder.supplier_profile_id == supplier_profile_id,
            StockOrder.is_deleted.is_(False),
            StockOrder.status == StockOrderStatus.CANCELLED,
            StockOrder.cancelled_by == "supplier",
        ).count()

        # Businesses with MORE THAN ONE accepted order. Moved here from
        # trust_stats_for_supplier (which see): a business coming back
        # is the clearest read a supplier has on whether the first
        # order went well, and that is feedback to act on rather than a
        # badge for strangers.
        #
        # Counted in SQL (group-by + having) rather than by loading
        # every order and tallying in Python -- the suppliers it
        # matters most for are the ones with the most rows.
        repeat_rows = (
            confirmed.with_entities(StockOrder.business_id)
            .group_by(StockOrder.business_id)
            .having(db.func.count(StockOrder.id) > 1)
            .all()
        )

        return {
            "decidedCount": len(decided),
            "acceptedCount": accepted_recent,
            "medianResponseHours": median_hours,
            "totalSalesCents": int(sales_cents or 0),
            "unitsSoldCount": int(units or 0),
            "ordersThisMonth": confirmed.filter(
                StockOrder.submitted_at >= utcnow() - timedelta(days=30)
            ).count(),
            "cancelledAfterConfirming": cancelled_after_confirming,
            "repeatBusinessCount": len(repeat_rows),
        }

    # ------------------------------------------------------------------
    # Trading history, grouped by the OTHER party.
    #
    # WHY GROUPED AND NOT PER ROW. My Connections and the supplier feed
    # both want "when did these two last trade" for every connection a
    # user has. Asking per connection is one query per row -- the feed
    # already did exactly that (a db.session.query inside a for loop in
    # supplier_sections), which is invisible at three connections and a
    # real problem at fifty. These return the whole picture in one query
    # and let the caller index into it.
    # ------------------------------------------------------------------

    #: A CART IS NOT AN ORDER, and a declined or cancelled one says
    #: nothing about a buying rhythm -- counting either would make a
    #: supplier who declines a lot look like they have loyal customers.
    #: This predicate was written twice before it lived here.
    RHYTHM_EXCLUDED_STATUSES = (
        StockOrderStatus.CART,
        StockOrderStatus.DECLINED,
        StockOrderStatus.CANCELLED,
    )

    #: STILL IN FLIGHT -- somebody is waiting on somebody.
    #: CONFIRMED is deliberately NOT here: there is no delivered or
    #: completed status in this model yet, so CONFIRMED is where a
    #: successful order ENDS, and calling it open would mean every
    #: connection permanently showed an outstanding order. When
    #: fulfilment states land, this set is what grows.
    OPEN_STATUSES = (
        StockOrderStatus.AWAITING_PAYMENT,
        StockOrderStatus.PENDING_SUPPLIER_APPROVAL,
    )

    @staticmethod
    def _counterparty_scope(business_id, supplier_profile_id):
        """Returns (the column naming the other party, the filter on us)."""
        if business_id is not None:
            return StockOrder.supplier_profile_id, StockOrder.business_id == business_id
        if supplier_profile_id is not None:
            return StockOrder.business_id, StockOrder.supplier_profile_id == supplier_profile_id
        raise ValueError("one of business_id or supplier_profile_id is required")

    @staticmethod
    def order_dates_by_counterparty(
        *, business_id: str | UUID | None = None, supplier_profile_id: str | UUID | None = None
    ) -> dict[str, List[datetime]]:
        """{other party id: [submitted_at, ...]} for everyone we have traded with."""
        other, mine = StockOrderRepository._counterparty_scope(business_id, supplier_profile_id)

        rows = (
            db.session.query(other, StockOrder.submitted_at)
            .filter(
                mine,
                StockOrder.submitted_at.isnot(None),
                StockOrder.status.notin_(StockOrderRepository.RHYTHM_EXCLUDED_STATUSES),
                StockOrder.is_deleted.is_(False),
            )
            .all()
        )

        grouped: dict[str, List[datetime]] = {}
        for counterparty_id, submitted_at in rows:
            grouped.setdefault(str(counterparty_id), []).append(submitted_at)
        return grouped

    @staticmethod
    def open_orders_by_counterparty(
        *, business_id: str | UUID | None = None, supplier_profile_id: str | UUID | None = None
    ) -> dict[str, List[StockOrder]]:
        """{other party id: every open order with them, OLDEST FIRST}.

        RETURNS THE LIST, NOT JUST THE FIRST. The caller needs both the
        oldest -- the one that has been waiting longest is the one
        somebody needs to act on -- and HOW MANY there are. A row that
        says "Order waiting" when three are waiting is not a summary,
        it is wrong, and the business cannot tell the difference.
        """
        other, mine = StockOrderRepository._counterparty_scope(business_id, supplier_profile_id)

        orders = (
            db.session.query(StockOrder)
            .filter(
                mine,
                StockOrder.status.in_(StockOrderRepository.OPEN_STATUSES),
                StockOrder.is_deleted.is_(False),
            )
            .order_by(StockOrder.submitted_at.asc())
            .all()
        )

        grouped: dict[str, List[StockOrder]] = {}
        for order in orders:
            grouped.setdefault(str(getattr(order, other.key)), []).append(order)
        return grouped

    @staticmethod
    def buyer_counts_for_products(product_ids) -> dict:
        """{product_id: how many DISTINCT businesses have bought it}.

        THE NUMBER A SHOPKEEPER ACTUALLY TRUSTS. "27 businesses bought
        this" is the only thing on a product card that is neither our
        opinion nor the supplier's -- it is what other shops did, and it
        is the one claim a competitor cannot fake into existence.

        BUSINESSES, NOT UNITS, and the difference is the whole point. A
        count of units lets one wholesale buyer manufacture a bestseller
        by ordering forty cases; a count of distinct businesses cannot
        be moved by anybody except more businesses.

        BATCHED, taking a list and returning a map. A per-card version
        would be the N+1 this file has spent three docstrings warning
        about.

        CONFIRMED ONLY, the same rule every other trading query here
        follows: a cart nobody checked out and an order a supplier
        declined are not purchases, and counting either would put a
        number on the card that never happened.
        """
        if not product_ids:
            return {}

        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        rows = (
            db.session.query(
                StockOrderItem.product_id,
                db.func.count(db.distinct(StockOrder.business_id)),
            )
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrderItem.product_id.in_(list(product_ids)),
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
            .group_by(StockOrderItem.product_id)
            .all()
        )
        return {product_id: count for product_id, count in rows}

    @staticmethod
    def units_sold_by_product(since, until=None) -> dict:
        """{product_id: units sold} inside a time window.

        THE INPUT TO "MOVING FAST". Called twice -- once for the recent
        window and once for the baseline before it -- and comparing the
        two is what separates a genuine spike from a product that has
        always sold well. A single window would just be a bestseller
        list wearing a more urgent label.

        UNITS HERE, NOT BUSINESSES, and deliberately the opposite choice
        to buyer_counts_for_products above. Velocity is about VOLUME
        moving: a shop doubling its usual order is exactly the signal,
        and counting distinct buyers would erase it.

        WINDOWED ON submitted_at, not created_at: a cart built in March
        and submitted in June is June's trade.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        query = (
            db.session.query(
                StockOrderItem.product_id,
                db.func.sum(StockOrderItem.quantity),
            )
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
                StockOrder.submitted_at >= since,
            )
        )
        if until is not None:
            query = query.filter(StockOrder.submitted_at < until)

        return {
            product_id: int(units or 0)
            for product_id, units in query.group_by(StockOrderItem.product_id).all()
        }

    @staticmethod
    def previously_ordered_product_ids_for_business(
        business_id: str | UUID, limit: int = 20
    ) -> List[UUID]:
        """Everything this business has had accepted, ACROSS ALL
        suppliers, most recently ordered first.

        THE SIBLING OF previously_ordered_product_ids, which takes a
        supplier and is right for a shopfront. "Buy it again" on the
        Community feed is not per shopfront -- it is the handful of
        things this shop actually restocks, wherever they come from --
        and calling the per-supplier version once per connection is the
        N+1 the trading-history queries above exist to avoid.

        SAME RULES, deliberately: CONFIRMED only, because a cart nobody
        checked out or an order a supplier declined is not something
        the business "ordered", and offering to reorder either would be
        offering to repeat something that never happened.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )

        rows = (
            db.session.query(
                StockOrderItem.product_id,
                db.func.max(StockOrder.submitted_at).label("last_ordered"),
            )
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrder.business_id == business_id,
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
            .group_by(StockOrderItem.product_id)
            .order_by(db.text("last_ordered DESC NULLS LAST"))
            .limit(limit)
            .all()
        )
        return [row.product_id for row in rows]

    # ------------------------------------------------------------------
    # What a business has actually bought.
    #
    # DELIBERATELY SUPPLIER-FREE RETURN SHAPES. These exist for the
    # demand engine, which may not import anything that knows who a
    # supplier is (tests/architecture/test_demand_independence.py) --
    # so the join to supplier_offers happens HERE, in a domain that is
    # allowed to make it, and what comes back is categories, dates and
    # amounts. The interface enforces the boundary rather than trusting
    # the caller to respect it.
    #
    # CONFIRMED ONLY, like every other history read in this file: a cart
    # nobody checked out or an order a supplier declined is not
    # something the business bought.
    # ------------------------------------------------------------------

    @staticmethod
    def category_purchase_counts(business_id: str | UUID, since: datetime = None) -> dict[str, int]:
        """{category: how many order lines} -- what this shop ACTUALLY buys.

        THE EVIDENCE HALF OF THE DEMAND MODEL. A declaration says what a
        shop believes it buys; this says what it has paid for.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )
        from src.domains.supplier.products.models.supplier_offer import SupplierOffer

        query = (
            db.session.query(SupplierOffer.category, db.func.count(StockOrderItem.id))
            .join(StockOrderItem, StockOrderItem.product_id == SupplierOffer.id)
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrder.business_id == business_id,
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
        )
        if since is not None:
            query = query.filter(StockOrder.submitted_at >= since)

        return {
            (category.value if hasattr(category, "value") else str(category)): count
            for category, count in query.group_by(SupplierOffer.category).all()
        }

    @staticmethod
    def category_purchase_counts_by_business() -> dict:
        """{business_id: {category: order lines}} for EVERY shop, in one
        query.

        THE AGGREGATE HALF. category_purchase_counts answers "what does
        this shop buy" for a feed; this answers "what does the market
        buy" for us, and the difference is one GROUP BY. Calling the
        per-shop version in a loop over ten thousand shops is the same
        N+1 that has been removed from this codebase twice.

        NO business_id FILTER AND NO LIMIT, deliberately: a gap report
        that sampled would under-count exactly the categories it exists
        to find. It is read by an operator on demand, never on a
        request path -- if that ever changes, this needs a cursor, not
        a smaller sample.

        SUPPLIER-FREE RETURN SHAPE, like its sibling. The join to
        supplier_offers happens HERE, in the orders domain, where it is
        allowed; what leaves this function is categories and counts, so
        the demand engine can read it without learning who sold
        anything (tests/architecture/test_demand_independence.py).
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )
        from src.domains.supplier.products.models.supplier_offer import SupplierOffer

        rows = (
            db.session.query(
                StockOrder.business_id,
                SupplierOffer.category,
                db.func.count(StockOrderItem.id),
            )
            .join(StockOrderItem, StockOrderItem.product_id == SupplierOffer.id)
            .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
            .filter(
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.is_deleted.is_(False),
                StockOrderItem.is_deleted.is_(False),
            )
            .group_by(StockOrder.business_id, SupplierOffer.category)
            .all()
        )

        counts: dict = {}
        for business_id, category, count in rows:
            if category is None:
                continue
            key = category.value if hasattr(category, "value") else str(category)
            counts.setdefault(str(business_id), {})[key] = count
        return counts

    @staticmethod
    def purchase_dates_and_totals(business_id: str | UUID) -> List[tuple]:
        """[(submitted_at, total_cents)] for every confirmed order, newest
        first.

        Two facts in one query because the demand engine wants both and
        they come from the same rows: WHEN they buy (cadence) and HOW
        MUCH (basket size). Splitting them would be two scans of the
        same table to answer one question about a shop's rhythm.
        """
        from src.domains.network.orders.models.stock_order import StockOrder, StockOrderStatus

        return (
            db.session.query(StockOrder.submitted_at, StockOrder.total_cents)
            .filter(
                StockOrder.business_id == business_id,
                StockOrder.status == StockOrderStatus.CONFIRMED,
                StockOrder.submitted_at.isnot(None),
                StockOrder.is_deleted.is_(False),
            )
            .order_by(StockOrder.submitted_at.desc())
            .all()
        )
