"""
StockOrderPayment repository -- ONLY talks to SQLAlchemy, no business
rules, same discipline as every other repository in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.extensions import db
from src.domains.network.orders.models.stock_order import StockOrder, StockOrderStatus
from src.domains.network.orders.models.stock_order_payment import StockOrderPayment, StockOrderPaymentStatus

# EVERY WAY OF PAYING THAT TRU CONNECT CANNOT SEE.
#
# One rail, three stored values, because the values are historical.
# DIRECT is what new orders record. CASH and PROOF_OF_PAYMENT are what
# orders recorded before the two were merged -- they were never really
# two rails (nothing stopped a buyer picking proof-of-payment for its
# higher cap and then handing over notes), but each row does faithfully
# record what that buyer selected at the time, so they are left alone
# rather than rewritten. All three count identically here, which is the
# whole point: what matters is not the instrument, it is that the money
# moved where TRU Connect could not observe it.
DIRECT_PAYMENT_METHODS = ("DIRECT", "CASH", "PROOF_OF_PAYMENT")

# Orders whose money never actually changed hands, so the spend they
# briefly reserved goes back to the business. See the full reasoning in
# sum_manual_payments_since's own docstring -- in particular why this is
# an EXCLUSION list and what that means for any status added later.
_STATUSES_THAT_RELEASE_SPEND = (
    StockOrderStatus.DECLINED,
    StockOrderStatus.CANCELLED,
)

# Money owed plus money paid. INCLUSION list here, unlike the exclusion
# list above, and for the opposite reason: a new PAYMENT status is far
# more likely to be another way of failing than another way of owing,
# so defaulting a new one to "does not consume the cap" is the safe
# direction. See sum_manual_payments_since for why DUE counts at all.
_STATUSES_THAT_CONSUME_SPEND = (
    StockOrderPaymentStatus.DUE,
    StockOrderPaymentStatus.SUCCEEDED,
)


class StockOrderPaymentRepository:
    @staticmethod
    def create(
        stock_order_id: str | UUID,
        payment_method: str,
        status: StockOrderPaymentStatus,
        amount_cents: int,
        platform_commission_cents: int,
        provider_transaction_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> StockOrderPayment:
        """Whether this is created as DUE (CASH/PROOF_OF_PAYMENT -- an
        obligation nobody has settled yet) or INITIATED (a real gateway
        attempt, awaiting its own webhook confirmation) is entirely the
        CALLER's decision, passed in via `status` -- this method just
        persists whatever's decided, never decides it itself."""
        now = datetime.now(timezone.utc)
        payment = StockOrderPayment(
            stock_order_id=stock_order_id,
            payment_method=payment_method,
            status=status,
            amount_cents=amount_cents,
            platform_commission_cents=platform_commission_cents,
            provider_transaction_id=provider_transaction_id,
            failure_reason=failure_reason,
            initiated_at=now,
            # completed_at means "this payment reached a final answer",
            # so only SUCCEEDED and FAILED get one. DUE and INITIATED
            # are both still open questions -- a DUE cash payment that
            # gets one here would be claiming a completion date for
            # money nobody has handed over.
            completed_at=now
            if status in (StockOrderPaymentStatus.SUCCEEDED, StockOrderPaymentStatus.FAILED)
            else None,
        )
        db.session.add(payment)
        db.session.commit()
        return payment

    @staticmethod
    def sum_manual_payments_since(business_id: str | UUID, since: datetime) -> int:
        """THE REAL MONTHLY-CUMULATIVE GUARANTEE this whole design
        exists for -- a live, date-bounded SUM query, not a stored
        counter. Mirrors shared/media/ledger's own
        total_bytes_since(account_id, since) exactly: no reset job, no
        scheduler, no drift risk, because the number IS the real rows,
        never a cache of them. Confirmed as the right pattern by
        finding that exact precedent already proven in this codebase
        before building this.

        WHAT IS COUNTED: DUE and SUCCEEDED -- money OWED plus money
        PAID. Not FAILED (a gateway said no) and not INITIATED (a
        gateway redirect still in flight, which may yet fail).

        COUNTING WHAT IS MERELY OWED IS THE POINT, not a compromise.
        The cap exists to bound how much unverified money moves
        through relationships on this platform, and a submitted order
        is that commitment. If only settled payments counted, a
        business could submit unlimited orders in parallel -- each one
        individually passing the check because none of the earlier
        ones had been paid yet -- and the cumulative cap would mean
        nothing at all.

        This used to read SUCCEEDED only, which gave the same answer
        for the wrong reason: manual payments were written SUCCEEDED
        at submission, so "settled" and "owed" were accidentally the
        same set. Splitting those two states apart (see
        StockOrderPaymentStatus) made the real intent something that
        had to be stated rather than inherited.

        WINDOWED ON initiated_at, NOT completed_at. A DUE payment has
        no completed_at at all -- nothing has completed -- so the old
        filter would have silently dropped every unsettled order out
        of the sum and handed every business an unlimited cap. Beyond
        not breaking, it is also the more correct field: a business
        that commits R5,000 on the 31st committed it in THAT month,
        and a payment must not migrate between months later just
        because that is when someone got round to confirming it.

        DECLINED AND CANCELLED ORDERS ARE EXCLUDED, and this was a real
        reported bug before it was a rule. A CASH / PROOF_OF_PAYMENT
        payment row is written SUCCEEDED at SUBMISSION -- before the
        supplier has even seen the order (see checkout_service, which
        does this because neither method has a verification step to
        wait on). Filtering on the PAYMENT's status alone therefore
        counted orders the supplier went on to refuse, and orders
        either side later pulled out of. A business that submitted
        R5,000 of cash orders and had every one of them declined was
        locked out of manual payments for the rest of the month over
        money that never changed hands.

        WHICH STATUSES STILL COUNT, and why each:
          PENDING_SUPPLIER_APPROVAL -- yes. The order is live and the
            money is committed pending a decision. If it did not
            count, a business could fire off unlimited orders in
            parallel, each individually passing the check, and the
            cumulative cap would mean nothing.
          CONFIRMED -- yes, obviously: a real, accepted order.
          DECLINED / CANCELLED -- no. Nothing was bought.

        EXCLUSION LIST, NOT AN INCLUSION LIST, deliberately. A new
        status added to StockOrderStatus later will COUNT by default.
        That is the safe direction: a future FULFILLED (or similar
        further-along) state must obviously consume the limit, and
        would silently stop doing so under an inclusion list. The
        direction that needs care is the opposite one -- if a status
        is ever added that means the money came BACK (a refund or
        reversal), it belongs in this list, and whoever adds it will be
        thinking about exactly that.

        CASH and PROOF_OF_PAYMENT summed TOGETHER, deliberately -- the
        cap is on total manual-payment exposure regardless of which of
        the two methods was used, closing the exact loophole caught
        during review (splitting one large order into several smaller
        ones, or switching methods, must never reset the real total).

        Joined through StockOrder for business_id -- stock_order_payments
        doesn't denormalize it; a join through two already-indexed
        tables (business_id on stock_orders, stock_order_id on
        stock_order_payments) is cheap enough not to need that
        duplication."""
        total = (
            db.session.query(db.func.coalesce(db.func.sum(StockOrderPayment.amount_cents), 0))
            .join(StockOrder, StockOrder.id == StockOrderPayment.stock_order_id)
            .filter(
                StockOrder.business_id == business_id,
                StockOrder.status.notin_(_STATUSES_THAT_RELEASE_SPEND),
                StockOrderPayment.payment_method.in_(DIRECT_PAYMENT_METHODS),
                StockOrderPayment.status.in_(_STATUSES_THAT_CONSUME_SPEND),
                StockOrderPayment.initiated_at >= since,
            )
            .scalar()
        )
        return int(total or 0)

    @staticmethod
    def sum_direct_receipts_for_supplier_since(supplier_profile_id: str | UUID, since: datetime) -> int:
        """The mirror image of sum_manual_payments_since, viewed from
        the other end of the trade: how much off-platform money has
        this SUPPLIER taken in this month, across every business
        buying from them.

        WHY BOTH ENDS NEED BOUNDING. The buyer-side cap limits what one
        business can move invisibly and does nothing about the total.
        Ten businesses each comfortably inside their own R5,000 send
        one supplier R50,000 that TRU Connect never sees -- and the
        exposure these caps exist to bound is the total crossing the
        platform, not any single buyer's share of it.

        DELIBERATELY THE SAME RULES AS THE BUYER-SIDE SUM, because it
        is the same money counted from the other side and the two must
        never disagree about what counts:
          * DUE and SUCCEEDED -- owed plus paid. See that method's
            docstring on why merely-owed has to count.
          * DECLINED and CANCELLED orders excluded -- nothing was
            bought, so nothing was received.
          * windowed on initiated_at, not completed_at -- a DUE payment
            has no completion date at all, and a payment must not
            migrate between months just because that is when someone
            got round to confirming it.

        If you change one of these, change the other. A supplier being
        told they have received money a buyer is not being charged for
        would be a genuinely confusing support conversation."""
        total = (
            db.session.query(db.func.coalesce(db.func.sum(StockOrderPayment.amount_cents), 0))
            .join(StockOrder, StockOrder.id == StockOrderPayment.stock_order_id)
            .filter(
                StockOrder.supplier_profile_id == supplier_profile_id,
                StockOrder.status.notin_(_STATUSES_THAT_RELEASE_SPEND),
                StockOrderPayment.payment_method.in_(DIRECT_PAYMENT_METHODS),
                StockOrderPayment.status.in_(_STATUSES_THAT_CONSUME_SPEND),
                StockOrderPayment.initiated_at >= since,
            )
            .scalar()
        )
        return int(total or 0)
