"""
SupplierOffer Service -- the SINGLE place a product row gets created or
updated. Per direct review: "don't have single-product validation !=
bulk-product validation... instead, one SupplierOffer Service, same
validation rules, one SupplierOffer DB." create_product/update_product are
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

import logging

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
from src.domains.supplier.products.algorithms.sku_generator import generate_sku
from src.extensions import db
from src.shared.constants.write_source import WriteSource
from src.domains.supplier.products.models.supplier_offer import SupplierOffer, ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
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


logger = logging.getLogger(__name__)


def _match_to_catalogue(
    product,
    *,
    name: str,
    category,
    barcode: Optional[str],
    brand: Optional[str],
    unit_quantity: Optional[int],
    unit_measure,
) -> None:
    """Attach this offer to the shared catalogue.

    THE GAP THIS CLOSES. Until now ONLY bulk import matched. A supplier
    adding products by hand -- the small supplier this product courts
    first -- produced offers that never reached the catalogue at all: no
    product_id, so no price comparison, no buy-it-again, no contribution
    to the shared library. Twenty hand-typed products were invisible to
    every feature the catalogue exists to power.

    NEVER RAISES, and never undoes the save. The offer is already
    written by the time this runs; a matching problem must cost the
    supplier nothing. This is the same rule the import worker has always
    followed -- an unmatched offer is exactly how every offer behaved
    before the catalogue existed.

    Imported locally because this is a cross-domain call (supplier ->
    catalogue, the permitted direction) and the module-level import
    would tie every products import to the matching domain's own graph.
    """
    from src.domains.catalogue.matching.services import linking_service

    try:
        linking_service.match_and_link(
            supplier_offer=product,
            name=name,
            category=category,
            barcode=barcode,
            brand=brand,
            unit_quantity=unit_quantity,
            unit_measure=unit_measure,
        )
    except Exception:  # noqa: BLE001 -- deliberately broad, see above
        logger.exception("catalogue matching failed for offer %s", getattr(product, "id", None))


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
    barcode: Optional[str] = None,
    brand: Optional[str] = None,
    commit: bool = True,
    source: WriteSource = WriteSource.APP,
) -> SupplierOffer:
    """commit=False is for BULK CALLERS ONLY (import). It hands the
    transaction to the caller so one file costs one fsync instead of
    one per row -- see SupplierOfferRepository.create for the numbers.
    Every interactive caller leaves it True and is unaffected."""
    _validate_common_fields(name, price_cents, compare_at_price_cents, description)

    sku = sku.strip() if sku else None
    if sku:
        if len(sku) > MAX_SKU_LENGTH:
            raise ProductValidationError(
                "Check the highlighted fields.", errors=[f"SKU must be {MAX_SKU_LENGTH} characters or fewer."]
            )
        if SupplierOfferRepository.sku_exists_for_supplier(supplier_profile_id, sku):
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

    product = SupplierOfferRepository.create(
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
        # Flushed rather than committed when matching still has to run,
        # so the offer has an id to attach a product to and the whole
        # thing lands in ONE transaction. A commit here followed by a
        # match would leave a window where the offer exists unmatched.
        commit=False,
        source=source,
    )

    _match_to_catalogue(
        product,
        name=name,
        category=category,
        barcode=barcode,
        brand=brand,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
    )
    if commit:
        db.session.commit()
    return product


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
    unit_quantity: Optional[int] = None,
    unit_measure: Optional[ProductUnit] = None,
    barcode: Optional[str] = None,
    brand: Optional[str] = None,
    commit: bool = True,
    source: WriteSource = WriteSource.APP,
) -> SupplierOffer:
    """commit=False: bulk callers only. See create_product."""
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")

    # A PACK SIZE BELOW 1 IS NOT A PACK. Blank is fine and common --
    # most products are genuinely sold as Each -- but "of 0" would
    # divide the per-unit price by nothing and put a meaningless
    # phrase on the product card.
    if unit_quantity is not None and unit_quantity < 1:
        raise ProductValidationError(
            "Check the highlighted fields.",
            errors=["How many are in the pack must be 1 or more, or left blank."],
        )
    # A measure with no quantity says nothing ("Case of bottles"), so
    # it is dropped rather than stored as half an answer.
    if not unit_quantity:
        unit_measure = None
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
        if sku != product.sku and SupplierOfferRepository.sku_exists_for_supplier(supplier_profile_id, sku):
            raise ProductValidationError(
                "Check the highlighted fields.", errors=[f'SKU "{sku}" is already used by another product.']
            )
    else:
        sku = product.sku

    product = SupplierOfferRepository.update(
        product,
        name=name.strip(),
        category=category,
        price_cents=price_cents,
        selling_unit=selling_unit,
        sku=sku,
        description=description.strip() if description else None,
        compare_at_price_cents=compare_at_price_cents,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
        commit=False,
    )

    # STAMPED ON EVERY EDIT, not only on create. `source` answers "who
    # wrote the value that is in this row NOW" -- an offer imported in
    # January and hand-corrected in March is an APP row, because the
    # correction is the thing a later conflict has to reason about.
    product.source = source

    # RE-MATCHED ON EVERY EDIT, and cheaply: match_and_link fingerprints
    # its inputs, so an edit that changed only the price does no
    # matching work at all. An edit that corrected the NAME or the
    # barcode is exactly when re-matching matters -- that is the
    # supplier fixing the thing that was stopping the match.
    _match_to_catalogue(
        product,
        name=name,
        category=category,
        barcode=barcode,
        brand=brand,
        unit_quantity=unit_quantity,
        unit_measure=unit_measure,
    )
    if commit:
        db.session.commit()
    return product


def get_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> SupplierOffer:
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return product


def list_products(
    supplier_profile_id: str | UUID,
    is_archived: Optional[bool] = False,
    search_term: Optional[str] = None,
) -> List[SupplierOffer]:
    return SupplierOfferRepository.list_for_supplier(
        supplier_profile_id, is_archived=is_archived, search_term=search_term
    )


def archive_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> SupplierOffer:
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return SupplierOfferRepository.archive(product)


def unarchive_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> SupplierOffer:
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return SupplierOfferRepository.unarchive(product)


def delete_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> SupplierOffer:
    """Soft delete only -- see SupplierOfferRepository.soft_delete's own
    docstring. The product vanishes from every screen instantly; the
    real row (and Inventory/ProductMedia rows still pointing at it)
    stays intact. Cloudinary's own real files get cleaned up later, on
    a schedule, by media/jobs/deleted_product_media_sweep.py -- never
    synchronously here, matching the exact same "don't do slow
    external-service work inside a request handler" discipline as
    every other media operation in this build."""
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise ProductNotFoundError("Product not found.")
    return SupplierOfferRepository.soft_delete(product)


def bulk_adjust_price(
    product_ids: List[str | UUID],
    supplier_profile_id: str | UUID,
    direction: str,
    adjustment_type: str,
    value: int,
) -> List[SupplierOffer]:
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
    products = SupplierOfferRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)

    def apply(current_price_cents: int) -> int:
        if adjustment_type == "PERCENTAGE":
            delta = round(current_price_cents * (value / 100))
        else:
            delta = value
        signed_delta = delta if direction == "INCREASE" else -delta
        return max(0, current_price_cents + signed_delta)

    return SupplierOfferRepository.bulk_adjust_price(products, apply)


def bulk_set_discount(
    product_ids: List[str | UUID],
    supplier_profile_id: str | UUID,
    discount_percent: int,
) -> List[SupplierOffer]:
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

    products = SupplierOfferRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)

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
                    "what TruConnect allows. Try a smaller discount, or set it individually."
                ],
            )
        return computed

    return SupplierOfferRepository.bulk_set_compare_at_price(products, compute_compare_at_price)


def bulk_archive(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[SupplierOffer]:
    products = SupplierOfferRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return SupplierOfferRepository.bulk_archive(products)


def bulk_unarchive(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[SupplierOffer]:
    products = SupplierOfferRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return SupplierOfferRepository.bulk_unarchive(products)


def bulk_delete(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[SupplierOffer]:
    """Same deferred-Cloudinary-cleanup reasoning as delete_product's
    own docstring, just for a whole batch at once."""
    products = SupplierOfferRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    return SupplierOfferRepository.bulk_soft_delete(products)
