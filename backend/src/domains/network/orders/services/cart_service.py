"""
cart_service -- everything about BUILDING a cart (add/update/remove
items, viewing it). Never touches a payment provider, never submits
anything -- that's checkout_service's own job, kept deliberately
separate so a bug in cart-building logic can never accidentally reach
a real payment call.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.products.services import product_media_service
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db
from src.domains.network.orders.errors import (
    CartAlreadySubmittedError,
    CartItemNotFoundError,
    CartNotFoundError,
    InvalidQuantityError,
    OutOfStockError,
    ProductNotFoundError,
    SupplierNotFoundError,
)
from src.domains.network.orders.models.stock_order import StockOrder, StockOrderStatus
from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository


def _get_valid_product(supplier_profile_id: str | UUID, product_id: str | UUID):
    """A product must genuinely belong to THIS cart's own supplier,
    and must not be archived -- see get_by_id_and_supplier's own
    docstring for the ownership check itself; is_archived is checked
    separately here since that repository method doesn't filter it
    (suppliers legitimately need to fetch their own archived products
    elsewhere; a cart never should). Not found, wrong supplier, and
    archived are all raised as the SAME error -- deliberately
    indistinguishable to the caller, same IDOR-safety reasoning as
    every other domain's own SUPPLIER_NOT_FOUND/PRODUCT_NOT_FOUND
    precedent.

    A REAL BUG FOUND AFTER DIRECT REPORT: this never actually checked
    stock at all -- an out-of-stock product could be added to a cart
    the same as an in-stock one. Fixed here, with its own distinct,
    clearly-named error (never the generic ProductNotFoundError,
    since "out of stock" and "doesn't exist" are genuinely different
    facts the frontend needs to tell apart to show the right message)."""
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product or product.is_archived:
        raise ProductNotFoundError("Product not found.")

    inventory = InventoryRepository.get_by_product_id(product.id)
    available = (inventory.quantity_on_hand - inventory.quantity_reserved) if inventory else 0
    if available <= 0:
        raise OutOfStockError(f"{product.name} is currently out of stock.", data={"productId": str(product.id)})

    return product


def _require_cart_status(stock_order: StockOrder) -> None:
    if stock_order.status != StockOrderStatus.CART:
        raise CartAlreadySubmittedError("This order has already been submitted and can no longer be changed.")


def _recalculate_and_save_total(stock_order: StockOrder) -> StockOrder:
    total = StockOrderRepository.recalculate_total(stock_order.id)
    return StockOrderRepository.save_total(stock_order, total)


def _collection_address_dict(supplier) -> Optional[dict]:
    """None unless the supplier has genuinely set a street-level
    address -- a dict of all-None fields would render as an empty
    address block, which reads as broken rather than as "not set yet"."""
    if supplier is None or not (supplier.collection_street or supplier.collection_suburb):
        return None
    return {
        "building": supplier.collection_building,
        "street": supplier.collection_street,
        "suburb": supplier.collection_suburb,
        "city": supplier.collection_city,
        "province": supplier.collection_province,
        "postalCode": supplier.collection_postal_code,
        "latitude": float(supplier.collection_latitude) if supplier.collection_latitude is not None else None,
        "longitude": float(supplier.collection_longitude) if supplier.collection_longitude is not None else None,
    }


def _build_cart_dict(stock_order: StockOrder, supplier) -> dict:
    """`supplier` is the SupplierProfile row, or None in the one case a
    cart can outlive its supplier (list_my_carts). Takes the ROW rather
    than a pre-extracted name so the "unknown supplier" fallback lives
    in exactly one place, and so the cart screen's own social top bar
    (EntityHeaderTitle: avatar + name) can read the brand image from
    the same lookup the name already came from -- ungated, same public
    shopfront reasoning as discovery_service's businessImageUrl."""
    db.session.refresh(stock_order)  # items relationship may be stale after a sibling write in this same request
    items = []
    for item in stock_order.items:
        if item.is_deleted:
            continue
        product = SupplierOfferRepository.get_by_id_and_supplier(item.product_id, stock_order.supplier_profile_id)
        items.append(
            {
                "productId": str(item.product_id),
                "productName": product.name if product else "(no longer available)",
                "images": product_media_service.list_approved_media(item.product_id) if product else [],
                "quantity": item.quantity,
                "priceCentsAtAddTime": item.price_cents_at_add_time,
                "lineTotalCents": item.quantity * item.price_cents_at_add_time,
                "isStale": product is None or product.is_archived,
            }
        )
    return {
        "id": str(stock_order.id),
        "supplierProfileId": str(stock_order.supplier_profile_id),
        "supplierName": supplier.business_name if supplier else "Unknown supplier",
        "supplierBusinessImageUrl": supplier.business_image_url if supplier else None,
        # CARRIED WITH THE NAME, EVERYWHERE THE NAME GOES. A cart can
        # outlive a supplier's verification: the curtain stops NEW
        # commerce with an unverified supplier and deliberately leaves
        # established trade alone, so a business holding a cart from a
        # supplier revoked yesterday still sees that cart. The tick
        # going missing is how they find out, and this is the field
        # that lets the cart and checkout screens say so.
        "supplierVerificationStatus": (
            supplier.verification_status.value if supplier else None
        ),
        # THE SUPPLIER'S OWN FULFILMENT TERMS, carried on the cart so
        # the checkout screen can honour them without a second request:
        # default to Collect when they don't deliver, and block/explain
        # under the minimum. checkout_service enforces both for real
        # (_validate_supplier_fulfilment_terms) -- these exist so the UI
        # can be honest BEFORE the business fills in a whole form.
        "supplierOffersDelivery": supplier.offers_delivery if supplier else False,
        "supplierMinimumOrderCents": supplier.minimum_order_cents if supplier else None,
        # Where to collect, for the checkout screen's COLLECT branch,
        # which until now could only say "will appear here once they've
        # added one".
        #
        # THIS IS NOW THE ONLY PLACE A COLLECTION ADDRESS REACHES AN
        # UNCONNECTED BUSINESS, and that is deliberate rather than an
        # oversight of v2 step 4. Connection stopped gating ordering, so
        # a business can now buy from a supplier it never connected to
        # -- and it cannot collect from an address it cannot see. The
        # exposure is still narrow: it takes a real cart with that
        # supplier, not browsing. The PROFILE endpoint's own address
        # gate was deliberately left alone, because widening that one
        # would change what every supplier who already opted into
        # sharing was actually agreeing to.
        "supplierCollectionAddress": _collection_address_dict(supplier),
        "status": stock_order.status.value,
        "totalCents": stock_order.total_cents,
        "itemCount": len(items),
        "items": items,
    }


def add_item(business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID, quantity: int) -> dict:
    """THE REAL PREREQUISITE "Add to Cart" needed to become -- was
    "Coming soon" everywhere in the product screens until this. Gets
    or creates the one, genuinely unique cart for this (business,
    supplier) pair (StockOrderRepository.get_or_create_cart's own
    concurrency guarantee), then adds this product to it -- or
    increments its quantity if it's already there."""
    if quantity < 1:
        raise InvalidQuantityError("Quantity must be at least 1.")

    supplier = SupplierProfileRepository.get_visible_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    product = _get_valid_product(supplier_profile_id, product_id)

    stock_order = StockOrderRepository.get_or_create_cart(business_id, supplier_profile_id)
    _require_cart_status(stock_order)
    StockOrderRepository.add_or_increment_item(stock_order.id, product.id, quantity, product.price_cents)
    stock_order = _recalculate_and_save_total(stock_order)

    return _build_cart_dict(stock_order, supplier)


def update_item_quantity(
    business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID, quantity: int
) -> dict:
    if quantity < 1:
        raise InvalidQuantityError("Quantity must be at least 1. Use remove instead to take an item out entirely.")

    supplier = SupplierProfileRepository.get_visible_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    stock_order = StockOrderRepository.get_cart(business_id, supplier_profile_id)
    if not stock_order:
        raise CartNotFoundError("No cart exists for this supplier.")
    _require_cart_status(stock_order)

    item = StockOrderRepository.get_item(stock_order.id, product_id)
    if not item:
        raise CartItemNotFoundError("This product isn't in your cart.")

    StockOrderRepository.set_item_quantity(item, quantity)
    stock_order = _recalculate_and_save_total(stock_order)

    return _build_cart_dict(stock_order, supplier)


def remove_item(business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID) -> dict:
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    stock_order = StockOrderRepository.get_cart(business_id, supplier_profile_id)
    if not stock_order:
        raise CartNotFoundError("No cart exists for this supplier.")
    _require_cart_status(stock_order)

    item = StockOrderRepository.get_item(stock_order.id, product_id)
    if not item:
        raise CartItemNotFoundError("This product isn't in your cart.")

    StockOrderRepository.delete_item(item)
    stock_order = _recalculate_and_save_total(stock_order)

    return _build_cart_dict(stock_order, supplier)


def clear_cart(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    """"Clear Cart" -- removes every item in one real batch operation
    (StockOrderRepository.delete_all_items), not a loop of individual
    removals. The cart row itself stays (still status=CART), just
    empty -- a business clearing their cart hasn't abandoned the
    supplier relationship, they've just started over."""
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    stock_order = StockOrderRepository.get_cart(business_id, supplier_profile_id)
    if not stock_order:
        raise CartNotFoundError("No cart exists for this supplier.")
    _require_cart_status(stock_order)

    StockOrderRepository.delete_all_items(stock_order.id)
    stock_order = _recalculate_and_save_total(stock_order)

    return _build_cart_dict(stock_order, supplier)


def get_cart(business_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[dict]:
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    stock_order = StockOrderRepository.get_cart(business_id, supplier_profile_id)
    if not stock_order:
        return None

    return _build_cart_dict(stock_order, supplier)


def list_my_carts(business_id: str | UUID) -> List[dict]:
    """The Account tab's own "My Checkouts" hub -- every supplier this
    business currently has an incomplete cart with, most recently
    updated first."""
    carts = StockOrderRepository.list_carts_for_business(business_id)
    results = []
    for cart in carts:
        supplier = SupplierProfileRepository.get_by_id(cart.supplier_profile_id)
        results.append(_build_cart_dict(cart, supplier))
    return results
