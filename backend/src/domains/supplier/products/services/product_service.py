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

from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
from src.domains.supplier.products.algorithms.sku_generator import generate_sku
from src.domains.supplier.products.models.product import Product, ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.domains.supplier.products.services.errors import ProductNotFoundError, ProductValidationError

MAX_NAME_LENGTH = 200
# Matches products/services/productMapper.ts's own MAX_PRICE_CENTS
# ceiling on the frontend -- kept in sync deliberately, not by
# coincidence. A price above this is almost certainly a data-entry
# error (a misplaced decimal), not a real product.
MAX_PRICE_CENTS = 100_000_000  # R1,000,000.00
MAX_DESCRIPTION_LENGTH = 1000
MAX_SKU_LENGTH = 50


def _validate_common_fields(
    name: str, price_cents: int, compare_at_price_cents: Optional[int] = None, description: Optional[str] = None
) -> None:
    errors: List[str] = []
    if not name or not name.strip():
        errors.append("Product name is required.")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"Product name must be {MAX_NAME_LENGTH} characters or fewer.")
    if price_cents is None or price_cents < 0:
        errors.append("Price must be zero or a positive amount.")
    elif price_cents > MAX_PRICE_CENTS:
        errors.append("Price is unrealistically large -- check for a decimal error.")
    if compare_at_price_cents is not None:
        if compare_at_price_cents < 0:
            errors.append("Compare-at price must be zero or a positive amount.")
        elif price_cents is not None and compare_at_price_cents <= price_cents:
            # A "sale" price that isn't actually lower than the real
            # price is either a mistake or meaningless -- caught here,
            # rather than letting a supplier publish something
            # confusing to whoever's browsing.
            errors.append("Compare-at price must be higher than the actual price to show as a discount.")
    if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer.")
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
    sku: Optional[str] = None,
    description: Optional[str] = None,
    compare_at_price_cents: Optional[int] = None,
) -> Product:
    _validate_common_fields(name, price_cents, compare_at_price_cents, description)

    sku = sku.strip() if sku else None
    if sku:
        if len(sku) > MAX_SKU_LENGTH:
            raise ProductValidationError(
                "Check the highlighted fields.", errors=[f"SKU must be {MAX_SKU_LENGTH} characters or fewer."]
            )
        if ProductRepository.sku_exists_for_supplier(supplier_profile_id, sku):
            raise ProductValidationError(
                "Check the highlighted fields.", errors=[f'SKU "{sku}" is already used by another product.']
            )
    else:
        # Left blank -- auto-filled so every product still has a
        # stable, reportable label to group sales/profit/order-count
        # by. See algorithms/sku_generator.py's own docstring.
        sku = generate_sku(supplier_profile_id)

    # NEVER supplied by a caller, NEVER editable once set -- see
    # algorithms/product_code_generator.py's own docstring.
    product_code = generate_product_code()

    return ProductRepository.create(
        supplier_profile_id=supplier_profile_id,
        name=name.strip(),
        category=category,
        price_cents=price_cents,
        selling_unit=selling_unit,
        sku=sku,
        product_code=product_code,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
        description=description.strip() if description else None,
        compare_at_price_cents=compare_at_price_cents,
    )


def update_product(
    product_id: str | UUID,
    supplier_profile_id: str | UUID,
    name: str,
    category: ProductCategory,
    price_cents: int,
    selling_unit: ProductUnit,
    sku: Optional[str] = None,
    description: Optional[str] = None,
    compare_at_price_cents: Optional[int] = None,
) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    _validate_common_fields(name, price_cents, compare_at_price_cents, description)

    # SKU is editable -- unlike product_code, which is never touched
    # here at all. None/blank means "leave whatever SKU this product
    # already has alone" -- update_product never re-generates a new
    # one on a supplier's behalf; only create_product does that.
    if sku is not None:
        sku = sku.strip()
        if not sku:
            raise ProductValidationError("Check the highlighted fields.", errors=["SKU cannot be blank once set."])
        if len(sku) > MAX_SKU_LENGTH:
            raise ProductValidationError(
                "Check the highlighted fields.", errors=[f"SKU must be {MAX_SKU_LENGTH} characters or fewer."]
            )
        if sku != product.sku and ProductRepository.sku_exists_for_supplier(supplier_profile_id, sku):
            raise ProductValidationError(
                "Check the highlighted fields.", errors=[f'SKU "{sku}" is already used by another product.']
            )
    else:
        sku = product.sku

    return ProductRepository.update(
        product,
        name=name.strip(),
        category=category,
        price_cents=price_cents,
        selling_unit=selling_unit,
        sku=sku,
        description=description.strip() if description else None,
        compare_at_price_cents=compare_at_price_cents,
    )


def get_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return product


def list_products(
    supplier_profile_id: str | UUID,
    is_archived: Optional[bool] = False,
    search_term: Optional[str] = None,
) -> List[Product]:
    return ProductRepository.list_for_supplier(
        supplier_profile_id, is_archived=is_archived, search_term=search_term
    )


def archive_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return ProductRepository.archive(product)


def unarchive_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Product:
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return ProductRepository.unarchive(product)


def delete_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Product:
    """Soft delete only -- see ProductRepository.soft_delete's own
    docstring. The product vanishes from every screen instantly; the
    real row (and Inventory/ProductMedia rows still pointing at it)
    stays intact. Cloudinary's own real files get cleaned up later, on
    a schedule, by media/jobs/deleted_product_media_sweep.py -- never
    synchronously here, matching the exact same "don't do slow
    external-service work inside a request handler" discipline as
    every other media operation in this build."""
    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return ProductRepository.soft_delete(product)


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


def bulk_set_discount(
    product_ids: List[str | UUID],
    supplier_profile_id: str | UUID,
    discount_percent: int,
) -> List[Product]:
    """Sets compare_at_price_cents on every selected product, computed
    from EACH product's own CURRENT price_cents -- price_cents itself
    is never touched. The real supplier problem this solves: putting a
    whole batch of products on sale by the same percentage without
    doing the "what number do I actually type" math by hand for each
    one, the same way bulk_adjust_price already spares suppliers that
    math for a straight price change.

    FORMULA: compare_at_price = price / (1 - discount/100), rounded to
    the nearest cent -- the exact inverse of how the frontend's own
    calculateDiscount.ts computes percent-off FROM a compare-at price,
    so a supplier who sets "20% off" here sees a real "20% OFF" badge
    on the result, not an off-by-rounding number.

    VALIDATED HERE, NOT TRUSTED FROM THE CLIENT -- discount_percent
    must be strictly between 0 and 100. 0 is not a real discount
    (nothing to set); 100 or more divides by zero or goes negative,
    which would violate this domain's own "compare_at_price must be
    strictly higher than price" rule by construction, not as an edge
    case worth silently allowing.
    """
    if discount_percent <= 0 or discount_percent >= 100:
        raise ProductValidationError(
            "Check the highlighted fields.", errors=["Discount must be between 1% and 99%."]
        )

    products = ProductRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)

    def compute_compare_at_price(current_price_cents: int) -> int:
        computed = round(current_price_cents / (1 - discount_percent / 100))
        if computed > MAX_PRICE_CENTS:
            # A genuinely rare combination (a price already near the
            # real ceiling, combined with a steep discount), but a
            # real one -- rejecting the WHOLE batch here (nothing
            # written, see bulk_set_compare_at_price's own docstring)
            # is more honest than silently clamping to a number that
            # doesn't match what the supplier actually asked for.
            raise ProductValidationError(
                "Check the highlighted fields.",
                errors=[
                    f"A {discount_percent}% discount would push one product's compare-at price above "
                    "what TRU Connect allows. Try a smaller discount, or set it individually."
                ],
            )
        return computed

    return ProductRepository.bulk_set_compare_at_price(products, compute_compare_at_price)


def bulk_archive(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[Product]:
    products = ProductRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return ProductRepository.bulk_archive(products)


def bulk_unarchive(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[Product]:
    products = ProductRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return ProductRepository.bulk_unarchive(products)


def bulk_delete(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[Product]:
    """Same deferred-Cloudinary-cleanup reasoning as delete_product's
    own docstring, just for a whole batch at once."""
    products = ProductRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return ProductRepository.bulk_soft_delete(products)
