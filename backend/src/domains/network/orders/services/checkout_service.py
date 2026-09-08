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

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domains.auth.models.user import User
from src.domains.business.business_profile.repositories.business_profile_repository import (
    BusinessProfileRepository,
)
from src.domains.network.orders.algorithms.order_reference_generator import generate_unique_order_reference
from src.domains.network.orders.notification_templates.stock_order_templates import (
    build_direct_receipts_threshold_notification,
    build_new_order_notification,
)
from src.shared.notifications.notifications import publish_notification
from src.domains.network.orders.services.commission import calculate_platform_commission_cents
from src.domains.business.order_limits.tiers import get_stock_order_limits
from src.domains.business.tiers.resolver import get_current_tier
from src.domains.supplier.order_limits.tiers import get_direct_payment_limits
# Aliased: both roles name their resolver get_current_tier, and they
# return deliberately different enums (BusinessTier vs Tier). Importing
# both under one name would be a silent, type-checker-invisible bug.
from src.domains.supplier.tiers.resolver import get_current_tier as get_current_supplier_tier
from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
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
    BelowMinimumOrderError,
    CartAlreadySubmittedError,
    CartNotFoundError,
    DeliveryNotOfferedError,
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

logger = logging.getLogger(__name__)

# PAYFAST exists on the enum (see StockOrderPaymentMethod's own
# docstring) but checkout_service never accepts it as a real choice
# yet. Adding it to this tuple is the ONE change needed once PayFast
# is genuinely wired -- the rest of this function's logic does not
# change, since it already delegates to whichever provider
# composition.py resolves for the chosen method.
#
# ONE OFFERABLE METHOD NOW. CASH and PROOF_OF_PAYMENT were merged into
# DIRECT -- see StockOrderPaymentMethod's own comment on why that
# distinction was never enforceable. The old values remain accepted on
# the way IN (an app build from before the merge, a resumed session)
# and are treated identically; they are simply never offered.
_AVAILABLE_PAYMENT_METHODS = (
    StockOrderPaymentMethod.DIRECT,
    StockOrderPaymentMethod.CASH,
    StockOrderPaymentMethod.PROOF_OF_PAYMENT,
)

# The same methods are subject to spending limits -- PAYFAST never is,
# since a real gateway confirms payment before the order proceeds, so
# the fraud/reliability concern these limits exist for doesn't apply
# to it.
_METHODS_SUBJECT_TO_LIMITS = _AVAILABLE_PAYMENT_METHODS


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
        product = SupplierOfferRepository.get_by_id_and_supplier(item.product_id, stock_order.supplier_profile_id)
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

    1. Per-transaction cap. ONE number now, across the whole direct
       rail -- the old split (a lower cap for cash, a higher one for
       proof-of-payment) rested on a distinction TRU Connect could
       never verify, and a buyer wanting the higher cap only had to
       tick the other box. See StockOrderTierLimits.
    2. Monthly cumulative cap, summed across every direct method
       together via a live query (StockOrderPaymentRepository.
       sum_manual_payments_since) -- no stored counter, no scheduler,
       no drift risk; the number IS the real historical rows. See that
       repository method's own docstring for the full reasoning,
       confirmed against the proven shared/media/ledger precedent
       before building this.
    3. Calendar-month window -- "this month" resets on the 1st, the
       common, intuitive reading of a monthly limit.

    THIS IS THE BUYER'S HALF ONLY. The supplier's own ceiling on what
    they may RECEIVE is checked separately, in
    _validate_supplier_receipt_limits -- ten buyers each inside their
    own limit would otherwise leave the other end unbounded.
    """
    limits = get_stock_order_limits(get_current_tier(business_id))

    per_transaction_cap = limits.direct_transaction_cap_cents
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


def _notify_supplier_of_receipt_threshold(
    supplier,
    already_received_cents: int,
    projected_total_cents: int,
    cap_cents: int,
    warn_at_fractions: tuple[float, ...],
) -> None:
    """Tell the supplier once, on the order that actually crosses a
    threshold.

    FIRES ON THE CROSSING, NOT ON BEING OVER. The check is "were we
    below this line before, and above it now" -- so one notification
    per threshold per month, on the order that did it. Testing
    "projected >= threshold" instead would send a fresh warning on
    every subsequent order for the rest of the month, which is how a
    useful warning becomes noise a supplier learns to swipe away.

    HIGHEST THRESHOLD ONLY. An order large enough to cross 75% and 90%
    at once sends one message about 90%, not two -- the lower one is
    already true and no longer the useful number.

    NEVER BLOCKS CHECKOUT. Wrapped because a notification failing is
    not a reason to fail an order that is otherwise perfectly valid;
    the money and the stock matter, the message does not.
    """
    crossed = [
        fraction
        for fraction in warn_at_fractions
        if already_received_cents < cap_cents * fraction <= projected_total_cents
    ]
    if not crossed:
        return

    try:
        supplier_user_id = supplier.supplier_id
        publish_notification(
            build_direct_receipts_threshold_notification(
                supplier_user_id=str(supplier_user_id),
                received_cents=projected_total_cents,
                cap_cents=cap_cents,
                fraction=max(crossed),
            )
        )
    except Exception:  # noqa: BLE001 -- see the docstring above
        logger.exception(
            "checkout: failed to send direct-receipts threshold notification for supplier_profile_id=%s",
            supplier.id,
        )


def _validate_supplier_accepts_method(supplier, method_enum: StockOrderPaymentMethod) -> None:
    """A supplier decides which payment rails they take, the same way
    they decide whether they deliver.

    ENFORCED HERE AND NOT ONLY IN THE UI, for exactly the reasons
    _validate_supplier_fulfilment_terms gives: a stale screen, a
    resumed session or a direct API call all reach this line, and the
    supplier may have changed the answer after the cart was built.

    THE HISTORICAL VALUES COUNT AS DIRECT. An app build from before
    CASH and PROOF_OF_PAYMENT were merged still sends those, and they
    are the same rail -- refusing them would break older clients over a
    rename.
    """
    is_direct = method_enum in _AVAILABLE_PAYMENT_METHODS

    if is_direct and not supplier.accepts_direct_payment:
        raise PaymentMethodNotAvailableError(
            f"{supplier.business_name} only accepts payment through TRU Connect. "
            "Choose that option to place this order."
        )

    if method_enum == StockOrderPaymentMethod.PAYFAST and not supplier.accepts_digital_payment:
        raise PaymentMethodNotAvailableError(
            f"{supplier.business_name} doesn't accept online payment. "
            "Choose to pay them directly instead."
        )


def _validate_supplier_receipt_limits(supplier, stock_order) -> None:
    """The supplier end of the direct-payment ceiling.

    WARNS ALWAYS, BLOCKS ONLY WHEN THE TIER SAYS SO. Today no tier
    blocks -- see DirectPaymentTierLimits.blocks_when_exceeded on why
    that is deliberate rather than unfinished: the cap exists to move
    suppliers onto the digital rail, and the gateway is not wired, so
    blocking now would stop a supplier trading rather than redirect
    them. The warning runs from day one regardless, so the limit is
    already familiar by the time it can bite.

    THE WARNING GOES TO THE SUPPLIER, NEVER THE BUYER. It is the
    supplier's ceiling, their tier and their decision to act on; a
    business told "this supplier is near their limit" learns something
    about someone else's account that is none of their business and
    that they cannot do anything about.
    """
    limits = get_direct_payment_limits(get_current_supplier_tier(supplier.id))

    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    already_received = StockOrderPaymentRepository.sum_direct_receipts_for_supplier_since(
        supplier.id, start_of_month
    )
    projected_total = already_received + stock_order.total_cents
    cap = limits.monthly_direct_receipts_cap_cents

    if projected_total > cap and limits.blocks_when_exceeded:
        publish(
            AuditEvent(
                event_name=BusinessAuditEvent.ORDER_LIMIT_EXCEEDED,
                domain=AuditDomain.BUSINESS,
                status=AuditStatus.FAILURE,
                metadata={
                    "supplier_profile_id": str(supplier.id),
                    "reason": "SUPPLIER_MONTHLY_RECEIPTS_LIMIT",
                    "already_received_this_month_cents": already_received,
                    "order_total_cents": stock_order.total_cents,
                    "monthly_limit_cents": cap,
                },
            )
        )
        # Worded for the BUYER, who is the one being stopped and who
        # did nothing wrong. It names no figures from the supplier's
        # account -- their monthly turnover is not a buyer's business.
        raise OrderLimitExceededError(
            f"{supplier.business_name} can't take more direct payments this month. "
            "Try again next month, or ask them about paying through TRU Connect.",
            data={"reason": "SUPPLIER_MONTHLY_RECEIPTS_LIMIT"},
        )

    _notify_supplier_of_receipt_threshold(
        supplier=supplier,
        already_received_cents=already_received,
        projected_total_cents=projected_total,
        cap_cents=cap,
        warn_at_fractions=limits.warn_at_fractions,
    )


def _validate_supplier_fulfilment_terms(supplier, stock_order, delivery_type: str) -> None:
    """The supplier's own two stated terms, enforced at the last
    possible moment -- right before a payment provider is called.

    Both are ALSO applied in the UI (the checkout screen defaults to
    COLLECT for a non-delivering supplier and blocks Continue under the
    minimum), but a client is never the gate: a stale screen, a resumed
    session, or a direct API call all reach here, and the supplier may
    have changed either term after the cart was built.

    Delivery is checked before the minimum on purpose -- "they don't
    deliver at all" is a more fundamental answer than "your order is
    too small", and being told to add stock to an order that could
    never be delivered would be actively misleading.

    offers_delivery IS TRI-STATE: only an EXPLICIT False blocks. NULL
    means the supplier hasn't stated their terms, and refusing delivery
    on the strength of an answer they never gave would remove working
    functionality from every supplier who predates the field -- which
    is exactly what happened when this was a plain boolean (31 checkout
    tests failed at once). See the column's own comment.
    """
    if (
        StockOrderDeliveryType(delivery_type) == StockOrderDeliveryType.DELIVER
        and supplier.offers_delivery is False
    ):
        raise DeliveryNotOfferedError(
            f"{supplier.business_name} only accepts collection orders. "
            "Choose Collect to place this order."
        )

    minimum = supplier.minimum_order_cents
    if minimum and stock_order.total_cents < minimum:
        shortfall = minimum - stock_order.total_cents
        raise BelowMinimumOrderError(
            f"{supplier.business_name} has a minimum order of R{minimum / 100:,.2f}. "
            f"Add R{shortfall / 100:,.2f} more to place this order.",
            data={
                "minimumOrderCents": minimum,
                "orderTotalCents": stock_order.total_cents,
                "shortfallCents": shortfall,
            },
        )


def submit_checkout(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    payment_method: str,
    delivery_type: str,
    delivery_address_text: Optional[str] = None,
    delivery_building: Optional[str] = None,
    delivery_street: Optional[str] = None,
    delivery_suburb: Optional[str] = None,
    delivery_city: Optional[str] = None,
    delivery_province: Optional[str] = None,
    delivery_postal_code: Optional[str] = None,
    delivery_latitude: Optional[float] = None,
    delivery_longitude: Optional[float] = None,
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
    _validate_supplier_fulfilment_terms(supplier, stock_order, delivery_type)

    method_enum = StockOrderPaymentMethod(payment_method)
    _validate_supplier_accepts_method(supplier, method_enum)

    if method_enum in _METHODS_SUBJECT_TO_LIMITS:
        # BOTH ENDS OF THE SAME TRADE. The buyer cap bounds what one
        # business moves invisibly; the supplier cap bounds the total
        # arriving at the other end, which ten buyers inside their own
        # limits would otherwise leave completely unbounded.
        _validate_spending_limits(business_id, stock_order, method_enum)
        _validate_supplier_receipt_limits(supplier, stock_order)

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
    # Structured fields are only ever meaningful for DELIVER -- a
    # COLLECT order has no business-entered address at all (it shows
    # the supplier's own, read straight from their profile), so these
    # simply stay None for COLLECT regardless of what was passed in,
    # rather than trusting the caller not to send stale values.
    if stock_order.delivery_type == StockOrderDeliveryType.DELIVER:
        stock_order.delivery_building = delivery_building
        stock_order.delivery_street = delivery_street
        stock_order.delivery_suburb = delivery_suburb
        stock_order.delivery_city = delivery_city
        stock_order.delivery_province = delivery_province
        stock_order.delivery_postal_code = delivery_postal_code
        stock_order.delivery_latitude = delivery_latitude
        stock_order.delivery_longitude = delivery_longitude
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
    # CASH/PROOF_OF_PAYMENT: DUE -- an obligation, not a settlement.
    #
    # This used to be written SUCCEEDED right here, which claimed money
    # had changed hands at the exact moment the business tapped
    # "Confirm order" -- before the supplier had even seen it. For cash
    # the money moves on delivery, days later, between two people in a
    # yard; nothing about that reaches this system. For proof of
    # payment it moves by bank transfer that TRU Connect never sees
    # either.
    #
    # DUE is what is actually true here and all this code can honestly
    # assert. Moving it to SUCCEEDED needs someone who was there to say
    # so -- the supplier confirming receipt, which does not exist yet --
    # or a gateway webhook, once PayFast is wired. A real gateway
    # payment would be created at INITIATED instead.
    StockOrderPaymentRepository.create(
        stock_order_id=stock_order.id,
        payment_method=method_enum.value,
        status=StockOrderPaymentStatus.DUE,
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
