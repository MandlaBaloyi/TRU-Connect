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
from src.domains.supplier.products.repositories.product_repository import ProductRepository
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
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
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


def _build_cart_dict(stock_order: StockOrder, supplier_name: str) -> dict:
    db.session.refresh(stock_order)  # items relationship may be stale after a sibling write in this same request
    items = []
    for item in stock_order.items:
        if item.is_deleted:
            continue
        product = ProductRepository.get_by_id_and_supplier(item.product_id, stock_order.supplier_profile_id)
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
        "supplierName": supplier_name,
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

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    product = _get_valid_product(supplier_profile_id, product_id)

    stock_order = StockOrderRepository.get_or_create_cart(business_id, supplier_profile_id)
    _require_cart_status(stock_order)
    StockOrderRepository.add_or_increment_item(stock_order.id, product.id, quantity, product.price_cents)
    stock_order = _recalculate_and_save_total(stock_order)

    return _build_cart_dict(stock_order, supplier.business_name)


def update_item_quantity(
    business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID, quantity: int
) -> dict:
    if quantity < 1:
        raise InvalidQuantityError("Quantity must be at least 1. Use remove instead to take an item out entirely.")

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

    StockOrderRepository.set_item_quantity(item, quantity)
    stock_order = _recalculate_and_save_total(stock_order)

    return _build_cart_dict(stock_order, supplier.business_name)


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

    return _build_cart_dict(stock_order, supplier.business_name)


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

    return _build_cart_dict(stock_order, supplier.business_name)


def get_cart(business_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[dict]:
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    stock_order = StockOrderRepository.get_cart(business_id, supplier_profile_id)
    if not stock_order:
        return None

    return _build_cart_dict(stock_order, supplier.business_name)


def list_my_carts(business_id: str | UUID) -> List[dict]:
    """The Account tab's own "My Checkouts" hub -- every supplier this
    business currently has an incomplete cart with, most recently
    updated first."""
    carts = StockOrderRepository.list_carts_for_business(business_id)
    results = []
    for cart in carts:
        supplier = SupplierProfileRepository.get_by_id(cart.supplier_profile_id)
        supplier_name = supplier.business_name if supplier else "Unknown supplier"
        results.append(_build_cart_dict(cart, supplier_name))
    return results
