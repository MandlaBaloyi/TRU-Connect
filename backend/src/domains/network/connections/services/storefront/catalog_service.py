"""
Browsing a supplier's stock catalogue, as a business sees it: the
category filter options, the paginated grid, "more from this supplier",
and one product in detail.

Browsing stays open to ANY authenticated business regardless of
connection status -- only ORDERING is gated (see ordering_gate).
Archived products are always excluded.
"""
from __future__ import annotations

import math
from typing import List, Optional
from uuid import UUID

from src.domains.network.connections.models.connection_request import ConnectionRequestStatus
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services.errors import (
    InvalidCatalogQueryError,
    ProductNotFoundError,
    SupplierNotFoundError,
)
from src.domains.network.connections.services.storefront.product_dto import (
    build_catalog_product_dicts,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)

VALID_CATALOG_SORT_OPTIONS = {"NEWEST", "NAME_ASC", "PRICE_ASC", "PRICE_DESC"}
MAX_CATALOG_PAGE_SIZE = 50
DEFAULT_CATALOG_PAGE_SIZE = 20


def get_supplier_product_categories(supplier_profile_id: str | UUID) -> List[str]:
    """The real fix for a real bug caught during review: this used to
    be derived on the FRONTEND from whichever products happened to be
    on the currently-loaded page, which broke the moment pagination
    existed. A dedicated, cheap, direct query -- correct regardless of
    page/sort/filter, and fetched once by the frontend rather than
    recomputed on every page change (a supplier's own category set
    doesn't change just because the business viewing it turned a
    page)."""
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    return ProductRepository.list_distinct_categories_for_supplier(supplier_profile_id)


def list_supplier_products(
    business_id: str | UUID,
    supplier_profile_id: str | UUID,
    page: int = 1,
    limit: int = DEFAULT_CATALOG_PAGE_SIZE,
    sort: str = "NEWEST",
    category: Optional[str] = None,
) -> dict:
    """Real, and now genuinely useful -- name/category/price/unit,
    matching Product's own grown shape (Phase 1: Products). Viewable by
    ANY authenticated business regardless of connection status --
    browsing stays open; only ordering is gated (can_place_order).
    Archived products excluded.

    business_id -- so this can ALSO carry contact at the top level
    (same gating as get_supplier_product's own: an ACTIVE connection
    AND the supplier's own share_contact_details opt-in, both
    required), for the "Contact Supplier" menu item, which needs
    contact info without requiring a business to first pick one
    specific product.

    PAGE/LIMIT/SORT/CATEGORY ARE THE REAL "PROTECT THE API, AND SCALE"
    FIX -- a supplier with hundreds of products used to mean one
    request returning every single row (and every image URL) at once.
    Sort and category filter are applied HERE, server-side, before
    pagination -- not left to the frontend to slice client-side,
    because once results are paginated, a client-side filter could
    only ever see whatever's on the current page, silently missing
    real matches sitting on other pages. limit is hard-capped at
    MAX_CATALOG_PAGE_SIZE regardless of what's requested -- the actual
    enforcement that makes this a genuine API protection, not just a
    UI suggestion a client could ignore by asking for limit=10000.
    """
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

    if page < 1:
        raise InvalidCatalogQueryError("Page must be 1 or greater.")
    if limit < 1:
        raise InvalidCatalogQueryError("Limit must be 1 or greater.")
    limit = min(limit, MAX_CATALOG_PAGE_SIZE)
    if sort not in VALID_CATALOG_SORT_OPTIONS:
        raise InvalidCatalogQueryError(f"Invalid sort value. Must be one of: {', '.join(sorted(VALID_CATALOG_SORT_OPTIONS))}.")
    if category is not None:
        from src.domains.supplier.products.models.product import ProductCategory

        try:
            ProductCategory(category)
        except ValueError:
            raise InvalidCatalogQueryError("Invalid category value.")

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    contact = None
    if is_active and supplier.share_contact_details:
        contact = {
            "whatsappNumber": supplier.whatsapp_number,
            "email": supplier.contact_email,
            "tiktokHandle": supplier.tiktok_handle,
        }

    products, total_count = ProductRepository.list_for_supplier_paginated(
        supplier_profile_id, page=page, limit=limit, sort=sort, category=category
    )
    total_pages = max(1, math.ceil(total_count / limit))

    # supplierName sits at the TOP LEVEL, not repeated inside every
    # product dict -- same value for every row, so duplicating it
    # would just be wasted bytes on every response. Same "certainty"
    # fix as get_supplier_product's own supplierName, applied one
    # screen earlier in the same flow -- a business browsing the whole
    # catalogue should know whose it is before ever tapping into one
    # specific product, not just once they get there.
    return {
        "supplierName": supplier.business_name,
        # For the social-style catalogue header (avatar + "<name> Stock"
        # + tick). Brand image is ungated -- same public-shopfront
        # reasoning as discovery_service.get_supplier_profile's
        # businessImageUrl.
        "supplierBusinessImageUrl": supplier.business_image_url,
        "supplierVerificationStatus": supplier.verification_status.value
        if supplier.verification_status
        else None,
        "contact": contact,
        "page": page,
        "totalPages": total_pages,
        "totalCount": total_count,
        "products": build_catalog_product_dicts(products),
    }


def list_related_products(business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID) -> dict:
    """"More from [Supplier]" -- see ProductRepository.
    list_related_products' own docstring for the full backfill
    reasoning. Genuinely related (same category) products come first,
    then any other product from this same supplier fills the
    remaining slots if fewer than 5 genuine matches exist -- confirmed
    after direct feedback: a supplier with real stock spread across
    many categories was showing nothing here far too often. Priority
    always goes to real relatedness; backfill only ever fills leftover
    slots, never displaces a genuine match. Same visibility rule as
    browsing the rest of the catalogue -- viewable by any
    authenticated business regardless of connection status.
    """
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product or product.is_archived:
        raise ProductNotFoundError("Product not found.")

    related = ProductRepository.list_related_products(supplier_profile_id, product.category, product.id, limit=5)
    return {"products": build_catalog_product_dicts(related)}


def get_supplier_product(business_id: str | UUID, supplier_profile_id: str | UUID, product_id: str | UUID) -> dict:
    """One product in real detail -- the supplier's own product-detail
    route is locked to role_required("supplier") plus an ownership
    check, so a business calling it would always be rejected outright,
    not just see the wrong data.

    Same visibility rules as list_supplier_products -- viewable by ANY
    authenticated business regardless of connection status, archived
    products excluded. get_by_id_and_supplier itself only filters
    is_deleted, not is_archived (it's shared with supplier-side
    mutation call sites that legitimately need to see archived rows),
    so the archived check happens here explicitly instead.

    ProductNotFoundError covers three cases identically -- genuinely
    doesn't exist, exists under a different supplier than the URL says,
    or exists but is archived -- same IDOR-safety reasoning as every
    other *NotFoundError in this domain.

    contact is gated server-side on a genuinely ACTIVE connection AND
    the supplier's own share_contact_details opt-in -- null (not an
    empty object) whenever EITHER is false, so a business browsing
    without a real relationship can never tell "not connected" apart
    from "connected but declined to share" from the response shape.
    """
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
    from src.domains.supplier.products.repositories.product_repository import ProductRepository
    from src.domains.supplier.products.services import product_media_service

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    product = ProductRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product or product.is_archived:
        raise ProductNotFoundError("Product not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    contact = None
    if is_active and supplier.share_contact_details:
        contact = {
            "whatsappNumber": supplier.whatsapp_number,
            "email": supplier.contact_email,
            "tiktokHandle": supplier.tiktok_handle,
        }

    inventory = InventoryRepository.get_by_product_id(product.id)
    available = (inventory.quantity_on_hand - inventory.quantity_reserved) if inventory else 0

    return {
        "id": str(product.id),
        "name": product.name,
        "supplierName": supplier.business_name,
        # For this screen's own social top bar (avatar + business name,
        # product name as the second line) -- a business deep in a
        # product page should still see whose product it is. Ungated
        # brand asset, same as everywhere else it appears.
        "supplierBusinessImageUrl": supplier.business_image_url,
        "contact": contact,
        "category": product.category.value,
        "priceCents": product.price_cents,
        "compareAtPriceCents": product.compare_at_price_cents,
        "sellingUnit": product.selling_unit.value,
        # Same real, direct answer as list_supplier_products' own
        # inStock -- never the exact quantity.
        "inStock": available > 0,
        "description": product.description,
        "sku": product.sku,
        "productCode": product.product_code,
        "images": product_media_service.list_approved_media(product.id),
    }
