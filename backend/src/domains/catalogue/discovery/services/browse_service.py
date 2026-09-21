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
    kind: Optional[str] = None,
    supplier: Optional[str] = None,
    mine_only: bool = False,
    sort: str = "name",
    limit: int = 24,
    offset: int = 0,
    max_line_cents: Optional[int] = None,
) -> dict:
    """Products a business can actually buy, in this category, from
    anyone visible.

    business_id IS OPTIONAL and the difference it makes is preference,
    never permission: with it, a shop sees its own supplier's offer
    where one exists. Without it the browse still works, which matters
    because this is the screen a brand-new user reaches first.

    max_line_cents is the same kind of preference: what this shop can
    plausibly spend on ONE product (demand/weighting.max_line_cents).
    It ORDERS the page and never trims it -- see _affordable_first.
    None means unknown, which most shops are, and is a no-op.
    """
    # "MY SUPPLIERS ONLY" IS A FILTER, NOT A PREFERENCE, and that is the
    # one place this function treats the connection as a gate. Everywhere
    # else in this file the connection only reorders -- browsing is open
    # at the platform level (V2_00 2.3) and a shop may always SEE
    # everything. Here the shop has explicitly asked for less, which is a
    # different thing from being shown less.
    supplier_ids = None
    if mine_only:
        supplier_ids = list(_incumbent_supplier_ids(business_id))

    # ONE SUPPLIER NARROWS WHATEVER IS ALREADY THERE, rather than
    # replacing it. Tapping a supplier chip while "my suppliers" is on
    # means "this one, of mine" -- and intersecting keeps that true
    # even if the chip is somehow stale, because a supplier who is not
    # in the list cannot be added to it by tapping.
    # THE SCOPE THE FACETS ARE COUNTED IN, deliberately WITHOUT the
    # single-supplier choice. Counting after it would leave exactly one
    # chip standing -- the one just tapped -- so the row collapses and
    # there is no way back to the others. The chips are the
    # ALTERNATIVES to the current choice; filtering them by that choice
    # is the same mistake brands_in avoided and suppliers_in did not.
    facet_supplier_ids = supplier_ids

    if supplier:
        supplier_ids = (
            [supplier] if supplier_ids is None else [s for s in supplier_ids if str(s) == supplier]
        )

    groups = catalogue_browse_repository.browse(
        category=category,
        categories=categories,
        search=search,
        kind=kind,
        supplier_ids=supplier_ids,
        sort=sort if sort in catalogue_browse_repository.SORTS else "name",
        limit=limit,
        offset=offset,
    )

    # THE FACETS COST A QUERY EACH, SO THEY ARE FETCHED ONCE PER RESULT
    # AND NOT ONCE PER PAGE. Offset zero is the first page of a given
    # filter; every scroll after it re-uses what the header already has,
    # which is the difference between two extra queries per BROWSE and
    # two per SCROLL.
    facets = {}
    if offset == 0:
        facets = {
            "total": catalogue_browse_repository.count(
                category=category,
                categories=categories,
                search=search,
                kind=kind,
                supplier_ids=supplier_ids,
            ),
            "kinds": catalogue_browse_repository.kinds_in(
                category=category,
                categories=categories,
                search=search,
                supplier_ids=facet_supplier_ids,
            ),
            # WHO IS SELLING IT, which becomes the useful axis the
            # moment a shop narrows to its own suppliers -- "which of
            # my four has this" decides whether an order is one
            # delivery or three. Sent always rather than only when
            # mine_only, so toggling the filter never costs a round
            # trip to populate the row that replaces the brands.
            "suppliers": catalogue_browse_repository.suppliers_in(
                category=category,
                categories=categories,
                search=search,
                supplier_ids=facet_supplier_ids,
            ),
        }

    if not groups:
        return {"products": [], "hasMore": False, **facets}

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
        "products": _affordable_first(
            _to_cards(chosen_by_group, in_stock), max_line_cents
        ),
        # A full page means there is probably another. Cheaper than a
        # COUNT over the whole catalogue on every scroll, and the only
        # cost of being wrong is one empty fetch at the end.
        "hasMore": len(groups) >= limit,
        **facets,
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


def _affordable_first(cards: List[dict], max_line_cents: Optional[int]) -> List[dict]:
    """Things this shop can plausibly buy, first. NEVER REMOVED.

    A DELIBERATE CHOICE AGAINST FILTERING, and the reasoning matters
    more than the code. Dropping every product above the ceiling would
    hide the R9,000 pallet from a spaza -- which is usually right and is
    catastrophic when it is wrong, because the shop is never told
    anything is missing. Flaw B.2 names silence as the one unacceptable
    outcome, and a rail that quietly omits half the category is silence
    with extra steps.

    Ordering gets the same result where it counts. The feed takes the
    first N cards, so the pallet falls off the end of a personalised
    rail on its own -- while a shop that deliberately taps "Grains" and
    scrolls still finds it, because there it is not a recommendation,
    it is the catalogue.

    STABLE, so whatever ranking produced the list survives inside each
    half.
    """
    if not max_line_cents:
        return cards
    return sorted(cards, key=lambda c: (c.get("priceCents") or 0) > max_line_cents)


def _to_cards(chosen_by_group: List, in_stock: set) -> List[dict]:
    """The card shape, matching the feed's FeedProduct so one component
    renders both."""
    from src.shared.algorithms import social_proof
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )
    from src.domains.supplier.products.services import product_media_service
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    # ONE COUNT QUERY FOR THE PAGE. Same batching rule as everything
    # else in this file -- the whole reason it exists is that the
    # alternative is four lookups per card.
    buyer_counts = StockOrderRepository.buyer_counts_for_products(
        [offer.id for offer, _ in chosen_by_group]
    )

    # ONE MEDIA QUERY FOR THE PAGE, not one per card. This file's own
    # docstring has always claimed it "batches everything before
    # deciding anything"; images were the exception nobody measured. A
    # 24-card page ran 40 SQL statements, 24 of them this.
    media_by_product = product_media_service.list_approved_media_for(
        [offer.id for offer, _ in chosen_by_group]
    )

    # One name lookup per SUPPLIER, not per card -- a page of 24 drinks
    # is typically a handful of wholesalers.
    names: dict = {}
    statuses: dict = {}

    cards = []
    for offer, group in chosen_by_group:
        supplier_id = offer.supplier_profile_id
        if supplier_id not in names:
            profile = SupplierProfileRepository.get_visible_by_id(supplier_id)
            names[supplier_id] = profile.business_name if profile else None
            statuses[supplier_id] = (
                profile.verification_status.value if profile and profile.verification_status else None
            )

        # A supplier that failed the curtain between the query and here
        # is dropped rather than rendered nameless.
        if names[supplier_id] is None:
            continue

        cards.append(
            {
                "id": str(offer.id),
                "supplierId": str(supplier_id),
                "supplierName": names[supplier_id],
                # SAME FIELD THE FEED SENDS, so one component renders
                # both surfaces and a supplier cannot appear ticked on
                # one screen and bare on the other.
                "supplierVerificationStatus": statuses.get(supplier_id),
                "name": offer.name,
                "category": offer.category.value if offer.category else None,
                "imageUrl": _first_image_url(media_by_product.get(offer.id)),
                "priceCents": offer.price_cents,
                "compareAtPriceCents": offer.compare_at_price_cents,
                "inStock": offer.id in in_stock,
                # THE RESOLVED CATALOGUE, MADE VISIBLE. Zero until
                # matching links these offers together -- and the day it
                # does, this card starts saying "also from 3 suppliers"
                # with no change here.
                "alternativeCount": offer_selection.alternatives_count(group, offer),
                # THE CHEAPEST OFFER IN THE GROUP, which is what makes
                # "also from 3 suppliers" worth reading. On its own that
                # line states a fact nobody can act on -- the card opens
                # ONE supplier's product page, so "which one?" has no
                # answer. Paired with a price it becomes the catalogue's
                # actual payoff: three wholesalers sell this, and here is
                # what the cheapest wants for it.
                "fromPriceCents": min(o.price_cents for o in group),
                # THE SAME BADGE THE FEED CARRIES, built from the same
                # rule, so one component renders both surfaces and the
                # wording cannot drift between them.
                "buyerCount": buyer_counts.get(offer.id) or None,
                "buyerLabel": social_proof.label(buyer_counts.get(offer.id)),
            }
        )
    return cards


def _first_image_url(images) -> Optional[str]:
    if not images:
        return None
    first = images[0]
    return first.get("url") if isinstance(first, dict) else first
