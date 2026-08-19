"""
Product Service -- the SINGLE place a product row gets created or
updated. Per direct review: "don't have single-product validation !=
bulk-product validation... instead, one Product Service, same
validation rules, one Product DB." create_product/update_product are
the only two write entry points this whole domain has; the future
Bulk Import worker calls these same two functions once per row rather
than growing its own copy. Neither knows the other exists.

Services own business rules; repositories own SQL (same split as
every other domain in this codebase). Validation lives here, not in
the route (a marshmallow schema catches malformed JSON shape -- wrong
types, missing required keys -- but "is this price sane" and "does
this supplier actually own this product" are business rules, not
schema shape, and belong here).
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.products.models.product import Product, ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services.errors import ProductNotFoundError, ProductValidationError

MAX_NAME_LENGTH = 200
# Matches products/services/productMapper.ts's own MAX_PRICE_CENTS
# ceiling on the frontend -- kept in sync deliberately, not by
# coincidence. A price above this is almost certainly a data-entry
# error (a misplaced decimal), not a real product.
MAX_PRICE_CENTS = 100_000_000  # R1,000,000.00


def _validate_common_fields(name: str, price_cents: int) -> None:
    errors: List[str] = []
    if not name or not name.strip():
        errors.append("Product name is required.")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"Product name must be {MAX_NAME_LENGTH} characters or fewer.")
    if price_cents is None or price_cents < 0:
        errors.append("Price must be zero or a positive amount.")
    elif price_cents > MAX_PRICE_CENTS:
        errors.append("Price is unrealistically large -- check for a decimal error.")
    if errors:
        raise ProductValidationError("Check the highlighted fields.", errors=errors)


def create_product(
    supplier_profile_id: str | UUID,
    name: str,
    category: ProductCategory,
    price_cents: int,
    selling_unit: ProductUnit,
    unit_quantity: Optional[int] = None,
    unit_measure: Optional[ProductUnit] = None,
) -> Product:
    _validate_common_fields(name, price_cents)
    return ProductRepository.create(
        supplier_profile_id=supplier_profile_id,
        name=name.strip(),
        category=category,
        price_cents=price_cents,
        selling_unit=selling_unit,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
    )


def update_product(
    product_id: str | UUID,
    supplier_profile_id: str | UUID,
    name: str,
    category: ProductCategory,
    price_cents: int,
    selling_unit: ProductUnit,
) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    _validate_common_fields(name, price_cents)
    return ProductRepository.update(
        product, name=name.strip(), category=category, price_cents=price_cents, selling_unit=selling_unit
    )


def get_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return product


def list_products(
    supplier_profile_id: str | UUID,
    include_archived: bool = False,
    search_term: Optional[str] = None,
) -> List[Product]:
    return ProductRepository.list_for_supplier(
        supplier_profile_id, include_archived=include_archived, search_term=search_term
    )


def archive_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return ProductRepository.archive(product)


def bulk_adjust_price(
    product_ids: List[str | UUID],
    supplier_profile_id: str | UUID,
    direction: str,
    adjustment_type: str,
    value: int,
) -> List[Product]:
    """direction: "INCREASE" | "DECREASE". adjustment_type: "PERCENTAGE"
    | "FIXED". value: whole percentage points if PERCENTAGE, integer
    CENTS if FIXED -- matching bulk-products' own PriceAdjustment
    contract on the frontend exactly (see that type's own docstring on
    why value is never rands directly). Clamped at 0, never negative --
    same rule the frontend's own applyPriceAdjustment algorithm
    already enforces client-side; enforced again here since a bulk
    price cut is exactly the kind of request this backend must never
    trust the client's own math for.
    """
    products = ProductRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)

    def apply(current_price_cents: int) -> int:
        if adjustment_type == "PERCENTAGE":
            delta = round(current_price_cents * (value / 100))
        else:
            delta = value
        signed_delta = delta if direction == "INCREASE" else -delta
        return max(0, current_price_cents + signed_delta)

    return ProductRepository.bulk_adjust_price(products, apply)


def bulk_archive(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[Product]:
    products = ProductRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return ProductRepository.bulk_archive(products)
