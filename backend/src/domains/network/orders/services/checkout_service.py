"""
checkout_service -- the ONLY place that submits a cart. Never mutates
a cart's own items (that's cart_service's job); never talks to a
payment provider directly except through get_payment_provider (never
imports ManualPaymentProvider or PayFastPaymentProvider by name).

Lives in domains/business/stock_order, NOT shared/checkout -- moved
here deliberately: building and submitting a cart is a real BUSINESS
action with real business rules attached (tier-based spending limits,
commission), not neutral infrastructure. shared/checkout stays the
neutral data model and payment-provider abstraction both business and
supplier depend on; this file is where business-specific DECISIONS
about that data actually get made. Same reasoning
domains/supplier/products already established for owning its own tier
limits rather than shared/media owning them.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domains.auth.models.user import User
from src.domains.business.business_profile.repositories.business_profile_repository import (
    BusinessProfileRepository,
)
from src.domains.network.orders.algorithms.order_reference_generator import generate_unique_order_reference
from src.domains.network.orders.notification_templates.stock_order_templates import build_new_order_notification
from src.shared.notifications.notifications import publish_notification
from src.domains.network.orders.services.commission import calculate_platform_commission_cents
from src.domains.business.order_limits.tiers import get_stock_order_limits
from src.domains.business.tiers.resolver import get_current_tier
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.shared.audit.audit import publish
from src.shared.audit.audit_types import AuditDomain, AuditEvent, AuditStatus
from src.shared.audit.event_types.business import BusinessAuditEvent
from src.domains.network.connections.models.connection_request import ConnectionRequestStatus
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.orders.errors import (
    CartAlreadySubmittedError,
    CartNotFoundError,
    EmptyCartError,
    OrderLimitExceededError,
    PaymentMethodNotAvailableError,
    StaleCartItemError,
    SupplierNotConnectedError,
    SupplierNotFoundError,
)
from src.domains.network.orders.models.stock_order import StockOrderDeliveryType, StockOrderPaymentMethod, StockOrderStatus
from src.domains.network.orders.models.stock_order_payment import StockOrderPaymentStatus
from src.domains.network.orders.providers.composition import get_payment_provider
from src.domains.network.orders.repositories.stock_order_payment_repository import StockOrderPaymentRepository
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository

# ONLY these two are actually offered in this pass -- PAYFAST exists
# on the enum (see StockOrderPaymentMethod's own docstring) but
# checkout_service itself never accepts it as a real choice yet.
# Extending this tuple is the ONE change needed once PayFast is
# genuinely wired -- the rest of this function's own logic doesn't
# need to change, since it already delegates to whichever provider
# composition.py resolves for the chosen method.
_AVAILABLE_PAYMENT_METHODS = (StockOrderPaymentMethod.CASH, StockOrderPaymentMethod.PROOF_OF_PAYMENT)

# The SAME two methods are subject to spending limits -- PAYFAST never
# is, since a real gateway confirms payment before the order proceeds,
# so the fraud/reliability concern these limits exist for doesn't
# apply to it.
_METHODS_SUBJECT_TO_LIMITS = (StockOrderPaymentMethod.CASH, StockOrderPaymentMethod.PROOF_OF_PAYMENT)


def _validate_cart_is_fresh(stock_order) -> None:
    """THE REAL "no mistake" CHECK -- re-verified at the actual moment
    of submission, never trusted from whatever was true when each item
    was originally added. A product could have been archived or
    deleted by the supplier at any point while sitting in someone's
    cart -- OR its stock could have simply run out, including from a
    DIFFERENT business's own order being submitted first while this
    one sat in a cart. Rejects the WHOLE checkout with a clear,
    specific list of which items are stale, rather than silently
    dropping them -- a business's own order should never be silently
    rewritten without their knowledge; they see exactly what's wrong
    and can remove the stale item themselves (cart_service.remove_item)
    before retrying.

    STOCK SUFFICIENCY IS RE-CHECKED HERE TOO, NOT JUST AT ADD-TO-CART
    TIME -- add_item's own check only proves a product was orderable
    the moment it was added; nothing re-confirms that's still true by
    the time checkout actually happens. Treated as the same kind of
    "staleness" as an archived product, not a separate error path --
    from a business's own perspective, both mean the same thing: this
    item can't be ordered right now, remove it."""
    stale_product_ids = []
    for item in stock_order.items:
        if item.is_deleted:
            continue
        product = ProductRepository.get_by_id_and_supplier(item.product_id, stock_order.supplier_profile_id)
        if not product or product.is_archived:
            stale_product_ids.append(str(item.product_id))
            continue

        inventory = InventoryRepository.get_by_product_id(product.id)
        available = (inventory.quantity_on_hand - inventory.quantity_reserved) if inventory else 0
        if available < item.quantity:
            stale_product_ids.append(str(item.product_id))

    if stale_product_ids:
        raise StaleCartItemError(
            "Some items in your cart are no longer available and need to be removed before you can check out.",
            data={"staleProductIds": stale_product_ids},
        )


def _validate_spending_limits(business_id: str | UUID, stock_order, method_enum: StockOrderPaymentMethod) -> None:
    """THE REAL, TIER-AWARE VERSION -- three real checks, not one flat
    number. Confirmed directly after review that a single per-
    transaction cap alone has a genuine hole: a business can simply
    place several smaller orders instead of one large one, and the
    SAME hole exists across payment methods too (a cap on cash alone
    just pushes every large order onto proof-of-payment). Both closed
    here.

    1. Per-transaction cap, DIFFERENT for cash vs proof-of-payment,
       matching the real tier numbers.
    2. Monthly cumulative cap, summed across BOTH manual methods
       together via a live query (StockOrderPaymentRepository.
       sum_manual_payments_since) -- no stored counter, no scheduler,
       no drift risk; the number IS the real historical rows. See that
       repository method's own docstring for the full reasoning,
       confirmed against the proven shared/media/ledger precedent
       before building this.
    3. Calendar-month window -- "this month" resets on the 1st, the
       common, intuitive reading of a monthly limit.
    """
    limits = get_stock_order_limits(get_current_tier(business_id))

    per_transaction_cap = (
        limits.cash_transaction_cap_cents
        if method_enum == StockOrderPaymentMethod.CASH
        else limits.proof_of_payment_transaction_cap_cents
    )
    if stock_order.total_cents > per_transaction_cap:
        publish(
            AuditEvent(
                event_name=BusinessAuditEvent.ORDER_LIMIT_EXCEEDED,
                domain=AuditDomain.BUSINESS,
                status=AuditStatus.FAILURE,
                metadata={
                    "business_id": str(business_id),
                    "reason": "PER_TRANSACTION_LIMIT",
                    "payment_method": method_enum.value,
                    "order_total_cents": stock_order.total_cents,
                    "limit_cents": per_transaction_cap,
                },
            )
        )
        raise OrderLimitExceededError(
            f"This order (R{stock_order.total_cents / 100:,.2f}) is over the "
            f"R{per_transaction_cap / 100:,.2f} per-transaction limit for {method_enum.value}.",
            data={
                "reason": "PER_TRANSACTION_LIMIT",
                "orderTotalCents": stock_order.total_cents,
                "limitCents": per_transaction_cap,
            },
        )

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    already_spent_this_month = StockOrderPaymentRepository.sum_manual_payments_since(business_id, start_of_month)
    projected_total = already_spent_this_month + stock_order.total_cents

    if projected_total > limits.monthly_manual_payment_cap_cents:
        publish(
            AuditEvent(
                event_name=BusinessAuditEvent.ORDER_LIMIT_EXCEEDED,
                domain=AuditDomain.BUSINESS,
                status=AuditStatus.FAILURE,
                metadata={
                    "business_id": str(business_id),
                    "reason": "MONTHLY_CUMULATIVE_LIMIT",
                    "payment_method": method_enum.value,
                    "already_spent_this_month_cents": already_spent_this_month,
                    "order_total_cents": stock_order.total_cents,
                    "monthly_limit_cents": limits.monthly_manual_payment_cap_cents,
                },
            )
        )
        raise OrderLimitExceededError(
            f"This order would bring your manual-payment spending this month to "
            f"R{projected_total / 100:,.2f}, over the R{limits.monthly_manual_payment_cap_cents / 100:,.2f} "
            f"monthly limit for your tier.",
            data={
                "reason": "MONTHLY_CUMULATIVE_LIMIT",
                "alreadySpentThisMonthCents": already_spent_this_month,
                "orderTotalCents": stock_order.total_cents,
                "monthlyLimitCents": limits.monthly_manual_payment_cap_cents,
            },
        )


def submit_checkout(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    payment_method: str,
    delivery_type: str,
    delivery_address_text: Optional[str] = None,
) -> dict:
    """The real "Checkout" action. Validates everything BEFORE ever
    calling a payment provider -- a provider's own job is only ever to
    handle the payment side of an ALREADY-valid cart (see
    PaymentProvider.process_checkout's own docstring).

    Also the real point where a StockOrderPayment record gets created
    -- see that model's own docstring on why this is a genuinely
    separate fact from the order itself. For CASH/PROOF_OF_PAYMENT
    this happens immediately with status=SUCCEEDED (neither has a
    verification step to wait on); a real PayFast attempt would create
    one at INITIATED instead, only moving to SUCCEEDED once its own
    webhook actually confirms it -- not reachable by anything in this
    pass.
    """
    if payment_method not in [m.value for m in _AVAILABLE_PAYMENT_METHODS]:
        raise PaymentMethodNotAvailableError(
            f"'{payment_method}' isn't available yet. Available now: {[m.value for m in _AVAILABLE_PAYMENT_METHODS]}."
        )

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    # THE REAL, CONFIRMED CONSTRAINT this domain never actually
    # enforced until now -- see SupplierNotConnectedError's own
    # docstring for the full reasoning. Browsing and building a cart
    # both stay allowed without an active connection (nothing changes
    # in cart_service.py); only the real financial commitment,
    # actually submitting an order, requires it.
    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    if not connection or connection.status != ConnectionRequestStatus.ACTIVE:
        raise SupplierNotConnectedError(
            "You need an active connection with this supplier before you can check out. "
            "Send a connection request first."
        )

    stock_order = StockOrderRepository.get_cart(business_id, supplier_profile_id)
    if not stock_order:
        raise CartNotFoundError("No cart exists for this supplier.")
    if stock_order.status != StockOrderStatus.CART:
        raise CartAlreadySubmittedError("This order has already been submitted.")

    real_items = [item for item in stock_order.items if not item.is_deleted]
    if not real_items:
        raise EmptyCartError("Your cart is empty.")

    _validate_cart_is_fresh(stock_order)

    method_enum = StockOrderPaymentMethod(payment_method)

    if method_enum in _METHODS_SUBJECT_TO_LIMITS:
        _validate_spending_limits(business_id, stock_order, method_enum)

    provider = get_payment_provider(method_enum)
    outcome = provider.process_checkout(stock_order, method_enum)

    supplier_code = supplier.supplier_code
    if not supplier_code:
        # A real, honest fallback for a supplier profile created
        # before this feature existed and somehow never backfilled --
        # never lets checkout itself fail over this; assigns one right
        # now instead, same generator every new supplier already gets.
        from src.domains.supplier.supplier_profile.algorithms.supplier_code_generator import (
            generate_unique_supplier_code,
        )

        supplier_code = generate_unique_supplier_code()
        supplier.supplier_code = supplier_code

    buyer_profile = BusinessProfileRepository.get_for_business(business_id)
    buyer_user = db.session.get(User, business_id)

    stock_order.payment_method = method_enum
    stock_order.delivery_type = StockOrderDeliveryType(delivery_type)
    stock_order.delivery_address_text = delivery_address_text
    stock_order.status = outcome.order_status
    # THE REAL, HUMAN-FACING ORDER REFERENCE -- assigned exactly once,
    # here, at the real moment of submission -- never at cart creation,
    # so an abandoned cart never consumes one. See that generator's
    # own docstring for the full "why 4+6 characters, why secrets, why
    # never sequential" reasoning.
    stock_order.order_reference = generate_unique_order_reference(supplier_code)
    # A REAL, DEDICATED timestamp -- never updated_at, which a future
    # supplier approve/decline would otherwise silently shift. Set
    # exactly once, here, and never touched again.
    stock_order.submitted_at = datetime.now(timezone.utc)
    # Buyer details, SNAPSHOTTED here -- what was true about this
    # business at the real moment of submission, not a live join that
    # could silently drift if the account changes later.
    if buyer_user:
        stock_order.buyer_name = " ".join(
            part for part in [buyer_user.first_name, buyer_user.last_name] if part
        ) or None
        stock_order.buyer_phone = (buyer_profile.phone if buyer_profile else None) or buyer_user.phone_number
        stock_order.buyer_email = (buyer_profile.email if buyer_profile else None) or buyer_user.email
    if buyer_profile:
        stock_order.buyer_business_name = buyer_profile.business_name
    db.session.commit()

    # THE REAL NOTIFICATION TRIGGER -- the supplier finds out the
    # moment a real order lands, not by polling. publish_notification
    # never blocks this request; a failure here must never turn a
    # genuinely successful checkout into an error, same reasoning as
    # every other publish() call in this codebase.
    publish_notification(
        build_new_order_notification(
            stock_order,
            supplier_user_id=str(supplier.supplier_id),
            buyer_business_name=stock_order.buyer_business_name or stock_order.buyer_name or "A business",
        )
    )

    # THE REAL RESERVATION -- see InventoryRepository.reserve_quantity's
    # own docstring for the full reasoning. Happens for every payment
    # method, not just manual ones -- a real PAYFAST order (once
    # wired) reaches CONFIRMED immediately and needs its own stock
    # reserved just as much as a PENDING_SUPPLIER_APPROVAL one does.
    # This is deliberately AFTER _validate_cart_is_fresh already
    # re-confirmed sufficient stock exists for every item -- this loop
    # only ever performs the increment, it never re-decides whether
    # reserving is valid.
    for item in real_items:
        inventory = InventoryRepository.get_by_product_id(item.product_id)
        if inventory:
            InventoryRepository.reserve_quantity(inventory, item.quantity)

    commission_cents = calculate_platform_commission_cents(stock_order.total_cents, method_enum)
    # CASH/PROOF_OF_PAYMENT: SUCCEEDED immediately -- neither has a
    # verification step to wait on. A real gateway payment (not
    # reachable here) would instead be created at INITIATED.
    StockOrderPaymentRepository.create(
        stock_order_id=stock_order.id,
        payment_method=method_enum.value,
        status=StockOrderPaymentStatus.SUCCEEDED,
        amount_cents=stock_order.total_cents,
        platform_commission_cents=commission_cents,
    )

    publish(
        AuditEvent(
            event_name=BusinessAuditEvent.ORDER_SUBMITTED,
            domain=AuditDomain.BUSINESS,
            status=AuditStatus.SUCCESS,
            metadata={
                "business_id": str(business_id),
                "supplier_profile_id": str(supplier_profile_id),
                "stock_order_id": str(stock_order.id),
                "payment_method": method_enum.value,
                "total_cents": stock_order.total_cents,
                "commission_cents": commission_cents,
            },
        )
    )

    return {
        "id": str(stock_order.id),
        "orderReference": stock_order.order_reference,
        "status": stock_order.status.value,
        "totalCents": stock_order.total_cents,
        "instructions": outcome.instructions,
        "redirectUrl": outcome.redirect_url,
    }
