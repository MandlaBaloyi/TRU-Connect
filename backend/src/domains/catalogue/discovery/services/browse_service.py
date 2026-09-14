"""
Browse the catalogue: the public face of catalogue/discovery.

WHAT THE CATEGORY CHIP FINALLY LANDS ON. Tapping "Drinks" routed to
SUPPLIER search and found shops; this finds stock.

IT BATCHES EVERYTHING BEFORE DECIDING ANYTHING. One query for the
offers, one for stock, one for the shop's own suppliers, one for
payment rails -- then offer_selection runs in memory over sets. The
alternative is four lookups per card, which is the N+1 removed twice
from this codebase in a single week.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.catalogue.discovery.repositories import catalogue_browse_repository
from src.domains.catalogue.discovery.services import offer_selection


def browse_category(
    *,
    business_id: Optional[str | UUID] = None,
    category: Optional[str] = None,
    categories: Optional[List[str]] = None,
    search: Optional[str] = None,
    limit: int = 24,
    offset: int = 0,
) -> dict:
    """Products a business can actually buy, in this category, from
    anyone visible.

    business_id IS OPTIONAL and the difference it makes is preference,
    never permission: with it, a shop sees its own supplier's offer
    where one exists. Without it the browse still works, which matters
    because this is the screen a brand-new user reaches first.
    """
    groups = catalogue_browse_repository.browse(
        category=category, categories=categories, search=search, limit=limit, offset=offset
    )
    if not groups:
        return {"products": [], "hasMore": False}

    all_offers = [offer for group in groups for offer in group]

    chosen_by_group = []
    in_stock = _in_stock_offer_ids(all_offers)
    incumbents = _incumbent_supplier_ids(business_id)

    for group in groups:
        offer = offer_selection.select(
            group,
            in_stock_ids=in_stock,
            incumbent_supplier_ids=incumbents,
        )
        if offer is not None:
            chosen_by_group.append((offer, group))

    return {
        "products": _to_cards(chosen_by_group, in_stock),
        # A full page means there is probably another. Cheaper than a
        # COUNT over the whole catalogue on every scroll, and the only
        # cost of being wrong is one empty fetch at the end.
        "hasMore": len(groups) >= limit,
    }


def _in_stock_offer_ids(offers: List) -> set:
    """One inventory read for the whole page.

    A missing inventory row means zero available -- the same default a
    real row would carry -- and is NEVER created as a side effect of
    somebody browsing. See InventoryRepository.list_by_product_ids.
    """
    from src.domains.supplier.inventory.repositories.inventory_repository import (
        InventoryRepository,
    )

    rows = InventoryRepository.list_by_product_ids([o.id for o in offers])
    return {
        row.product_id
        for row in rows
        if (row.quantity_on_hand - row.quantity_reserved) > 0
    }


def _incumbent_supplier_ids(business_id) -> set:
    """Suppliers this shop already has an active connection with.

    PREFERENCE, NOT PERMISSION. Browsing is open (V2_00 2.3); this only
    decides whose offer leads when several carry the same product, so
    the feed does not quietly move a shop off a supplier it already
    trades with.
    """
    if business_id is None:
        return set()

    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )

    return {
        str(r.supplier_profile_id)
        for r in ConnectionRequestRepository.list_active_for_business(business_id)
    }


def _to_cards(chosen_by_group: List, in_stock: set) -> List[dict]:
    """The card shape, matching the feed's FeedProduct so one component
    renders both."""
    from src.domains.supplier.products.services import product_media_service
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    # One name lookup per SUPPLIER, not per card -- a page of 24 drinks
    # is typically a handful of wholesalers.
    names: dict = {}

    cards = []
    for offer, group in chosen_by_group:
        supplier_id = offer.supplier_profile_id
        if supplier_id not in names:
            profile = SupplierProfileRepository.get_visible_by_id(supplier_id)
            names[supplier_id] = profile.business_name if profile else None

        # A supplier that failed the curtain between the query and here
        # is dropped rather than rendered nameless.
        if names[supplier_id] is None:
            continue

        images = product_media_service.list_approved_media(offer.id)
        cards.append(
            {
                "id": str(offer.id),
                "supplierId": str(supplier_id),
                "supplierName": names[supplier_id],
                "name": offer.name,
                "category": offer.category.value if offer.category else None,
                "imageUrl": _first_image_url(images),
                "priceCents": offer.price_cents,
                "compareAtPriceCents": offer.compare_at_price_cents,
                "inStock": offer.id in in_stock,
                # THE RESOLVED CATALOGUE, MADE VISIBLE. Zero until
                # matching links these offers together -- and the day it
                # does, this card starts saying "also from 3 suppliers"
                # with no change here.
                "alternativeCount": offer_selection.alternatives_count(group, offer),
            }
        )
    return cards


def _first_image_url(images) -> Optional[str]:
    if not images:
        return None
    first = images[0]
    return first.get("url") if isinstance(first, dict) else first
