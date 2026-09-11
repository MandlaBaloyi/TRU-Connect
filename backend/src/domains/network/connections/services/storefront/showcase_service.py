"""
The brand profile's product showcase -- the category strips a business
sees on a supplier's profile, before (or instead of) opening the full
catalogue.

Grouping lives here; ORDERING lives in ranking.py (pure). This module
owns anything that needs the database, including -- when best-selling
lands -- fetching the order counts and handing them to ranking.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.domains.network.connections.services.errors import SupplierNotFoundError
from src.domains.network.connections.services.storefront.product_dto import (
    build_catalog_product_dicts,
)
from src.domains.network.connections.services.storefront.ranking import showcase_sort_key
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)

SHOWCASE_MAX_CATEGORIES = 5
SHOWCASE_PER_CATEGORY = 6


def list_profile_products(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    """The category showcase on the supplier's brand profile -- their
    real product categories (biggest first, max 5), each a small strip.

    RULE 1: a product with no APPROVED image never appears here -- the
    profile is a storefront, and a blank card undermines it (the full
    catalogue, browsed deliberately, still shows every product with a
    placeholder). RULE 2: pinned products (the supplier's own ⋮-menu
    "feature this" picks) float to the front of their own category's
    strip. Same enriched per-product shape as the full catalogue
    (build_catalog_product_dicts: compareAtPriceCents, inStock,
    approved-only images).

    business_id is accepted (currently unused) for signature symmetry
    with every other business-facing read in this module.
    """
    from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
    from src.domains.supplier.supplier_profile.services import pinned_products_service

    supplier = SupplierProfileRepository.get_visible_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    products = SupplierOfferRepository.list_for_supplier(supplier_profile_id, is_archived=False)
    dicts = build_catalog_product_dicts(products)
    imaged = [d for d in dicts if d["images"]]
    pinned_ids = {str(pid) for pid in pinned_products_service.list_pinned_product_ids(supplier_profile_id)}
    return {"categories": _group_profile_showcase(imaged, pinned_ids)}


def _group_profile_showcase(imaged_dicts: List[dict], pinned_ids: set) -> List[dict]:
    """Pure grouping + ranking over the already-enriched,
    already-image-filtered product dicts. Buckets by category, ranks
    categories by how many imaged products each has (tie-break: the
    canonical ProductCategory order, so the result is stable), keeps the
    biggest SHOWCASE_MAX_CATEGORIES, then orders within each kept bucket
    by showcase_sort_key, capped at SHOWCASE_PER_CATEGORY.

    Within-bucket order used to be just "pinned first, then whatever
    order the query returned" -- effectively arbitrary beyond the pins.
    See showcase_sort_key for the real ranking that replaced it and
    for why it uses supplier-owned signals only."""
    from src.domains.supplier.products.models.supplier_offer import ProductCategory

    canonical_order = {c.value: i for i, c in enumerate(ProductCategory)}

    buckets: dict[str, List[dict]] = {}
    for d in imaged_dicts:
        buckets.setdefault(d["category"], []).append(d)

    ranked = sorted(
        buckets.items(),
        key=lambda kv: (-len(kv[1]), canonical_order.get(kv[0], len(canonical_order))),
    )[:SHOWCASE_MAX_CATEGORIES]

    out = []
    for category, items in ranked:
        # sorted() is STABLE, so products that tie on every key above
        # keep the caller's newest-first order -- that IS the recency
        # tie-break, see showcase_sort_key point 4.
        ordered = sorted(items, key=lambda d: showcase_sort_key(d, pinned_ids))
        out.append({"category": category, "products": ordered[:SHOWCASE_PER_CATEGORY]})
    return out


# ---------------------------------------------------------------------------
# Ordering gate -- agreed during architecture review, reconciling an
# earlier (wrong) proposal that would have gated CONNECTION itself on
# supplier verification. Verification doesn't functionally exist yet, so
# gating connection on it would make every supplier permanently
# unconnectable. The actual gate belongs one step later, on ORDERING,
# and depends on TWO things: (1) an ACTIVE connection, and (2) the
# supplier having at least one real product -- there is nothing to
# order from an empty catalogue.
# ---------------------------------------------------------------------------
