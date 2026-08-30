"""
StockOrderPayment repository -- ONLY talks to SQLAlchemy, no business
rules, same discipline as every other repository in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.extensions import db
from src.domains.network.orders.models.stock_order import StockOrder
from src.domains.network.orders.models.stock_order_payment import StockOrderPayment, StockOrderPaymentStatus


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
        """Whether this is created as already-SUCCEEDED (CASH/
        PROOF_OF_PAYMENT -- no verification step to wait on) or
        INITIATED (a real gateway attempt, awaiting its own webhook
        confirmation) is entirely the CALLER's decision, passed in via
        `status` -- this method just persists whatever's decided,
        never decides it itself."""
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
            completed_at=now if status != StockOrderPaymentStatus.INITIATED else None,
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

        SUCCEEDED only -- a FAILED or still-INITIATED payment attempt
        never counted against a business's own spending; only money
        that's actually, successfully moved.

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
                StockOrderPayment.payment_method.in_(["CASH", "PROOF_OF_PAYMENT"]),
                StockOrderPayment.status == StockOrderPaymentStatus.SUCCEEDED,
                StockOrderPayment.completed_at >= since,
            )
            .scalar()
        )
        return int(total or 0)
