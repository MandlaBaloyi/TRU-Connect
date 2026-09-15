"""
The full list behind each rail.

WHY THIS EXISTS. A rail is a preview -- twelve cards with an arrow at
the end (V2_17 Part 3.1). This is what the arrow leads to, and the
reason it is a SERVICE rather than five more functions in sections.py
is that the two surfaces must agree: a "see all" screen that ranked
differently from the rail it opened from would be a bug the reader
notices immediately and nobody else ever sees in a test.

SO THE GATHERING LIVES HERE AND THE SHAPING LIVES IN sections.py. The
rail asks this module for a short list and turns it into a rail; the
detail screen asks for a long one and paginates it. One rule, two
lengths, and the rule is here.

EVERY FUNCTION RETURNS THE FULL RANKED SET, uncapped and
un-interleaved. Deciding how many of one supplier's cards may appear is
the caller's business because it differs by surface (interleave.arrange
for a rail; a wider ceiling for a screen with fifty slots), and baking
it in here would have made the rail's anti-domination rule invisible
from the rail.

NOTHING HERE APPLIES A TIER. The detail screens rank exactly as the
rails do, and the placement module that will eventually break ties
(V2_16) is not wired into either yet.
"""
from __future__ import annotations

from datetime import timedelta
from typing import List, Optional, Tuple

from src.core.base_model import utcnow
from src.domains.network.community.algorithms import velocity
from src.domains.network.community.business.cards import feed_products
from src.domains.network.community.business.queries import (
    connected_supplier_ids,
    visible_offers,
)
from src.shared.algorithms import distance

#: The most any detail screen returns in one page.
#:
#: FIFTY, and it is a page size rather than a total: the screens scroll
#: and fetch again. It is large enough that a shopkeeper scrolling with
#: a thumb does not hit the end of a page every few seconds, and small
#: enough that one response over a rural connection is not a wait.
PAGE_SIZE = 50

#: How far a supplier can be and still count as collectable. Mirrors
#: sections.MAX_COLLECTION_KM -- imported there from here so the rail
#: and the screen cannot disagree about what "near" means.
#:
#: 25km covers a peri-urban shop reaching the nearest town's wholesale
#: strip and excludes the next city. A GUESS, falsified by shops
#: routinely collecting from further or ignoring everything past 10km.
MAX_COLLECTION_KM = 25.0


def buy_it_again_cards(business_id, *, limit: int = PAGE_SIZE) -> List[dict]:
    """Everything this shop has ordered before, most recent first.

    NOT CAPPED PER SUPPLIER AT ANY LENGTH (V2_17 Q3). It is their own
    confirmed history: a wholesaler appearing often is a fact about
    their trading, and recency order is information that interleaving
    would destroy.
    """
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    product_ids = StockOrderRepository.previously_ordered_product_ids_for_business(
        business_id, limit=limit * 2
    )
    if not product_ids:
        return []
    return feed_products(visible_offers(product_ids))


def moving_fast_cards(business_id, *, limit: int = PAGE_SIZE) -> List[dict]:
    """Products rising faster than their own past, in the categories
    this shop buys.

    IT ASKS THE DEMAND ENGINE FIRST, exactly as the rail does. An
    unfiltered version would be a platform leaderboard wearing a
    personal title -- and is also how one wholesaler's volume would
    start deciding what everybody sees.
    """
    from src.domains.business.demand.services import needs_service
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    needs = needs_service.needs_for(business_id)
    if not needs.is_known:
        return []

    now = utcnow()
    recent_since = now - timedelta(days=velocity.RECENT_DAYS)
    baseline_since = recent_since - timedelta(days=velocity.BASELINE_DAYS)

    recent = StockOrderRepository.units_sold_by_product(since=recent_since)
    if not recent:
        return []
    baseline = StockOrderRepository.units_sold_by_product(
        since=baseline_since, until=recent_since
    )

    # Over-fetch: the category filter below removes candidates, and so
    # does whatever ceiling the caller applies afterwards.
    rising = velocity.rising_products(recent, baseline, limit=limit * 4)
    if not rising:
        return []

    wanted = set(needs.category_values)
    pairs = [
        (offer, name, status)
        for offer, name, status in visible_offers(rising)
        if offer.category and offer.category.value in wanted
    ]
    return feed_products(pairs)


def stock_for_you_cards(business_id, *, limit: int = PAGE_SIZE) -> List[dict]:
    """The demand engine's full answer: products in what this shop
    buys, priced for what it can spend."""
    from src.domains.business.demand.services import needs_service
    from src.domains.catalogue.discovery.services import browse_service

    needs = needs_service.needs_for(business_id)
    if not needs.is_known:
        return []

    result = browse_service.browse_category(
        business_id=business_id,
        categories=needs.category_values,
        limit=limit * 3,
        max_line_cents=needs.max_line_cents,
    )
    products = result.get("products") or []

    return strongest_needs_first(products, needs)


def strongest_needs_first(products: List[dict], needs) -> List[dict]:
    """Open the rail with the category this shop needs MOST.

    THE CATALOGUE HAS NO OPINION ABOUT THIS SHOP, and should not: it
    returned everything across eleven categories in whatever order the
    query produced. The engine is the only thing that knows bread
    outranks phone chargers HERE, so the ordering belongs on this side
    of the call.

    ZERO EXTRA QUERIES. The weights are already in hand and every card
    already carries its category -- asking the catalogue per category
    instead would be the N+1 this codebase has removed twice (flaw B.4).

    STABLE, so affordability ordering from browse_service survives
    inside each category.
    """
    weights = needs.weight_by_category
    return sorted(products, key=lambda p: -weights.get(p.get("category"), 0.0))


def collect_near_you_suppliers(business_id) -> List[Tuple[float, object]]:
    """(km, profile) for every visible supplier inside the collection
    radius, nearest first.

    RETURNS DISTANCES WITH THE PROFILES because the caller needs both
    and recomputing them would be the same arithmetic twice.

    STRICTLY DISTANCE-ORDERED, at every tier, forever (V2_17 Q5). This
    is the only surface that prints the number it is sorted by, so any
    reordering is a contradiction the reader is holding.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter
    from src.extensions import db

    profile = BusinessProfileRepository.get_for_business(business_id)
    if profile is None or profile.latitude is None or profile.longitude is None:
        return []

    candidates = (
        db.session.query(SupplierProfile)
        .filter(
            visible_filter(),
            SupplierProfile.is_deleted.is_(False),
            SupplierProfile.collection_latitude.isnot(None),
            SupplierProfile.collection_longitude.isnot(None),
        )
        .all()
    )

    measured: List[Tuple[float, object]] = []
    for candidate in candidates:
        km = distance.km_between(
            profile.latitude,
            profile.longitude,
            candidate.collection_latitude,
            candidate.collection_longitude,
        )
        if km is None:
            continue
        # THE CEILING, not just the sort: "near you" that includes
        # another province is a lie the title tells.
        if km > MAX_COLLECTION_KM:
            continue
        measured.append((km, candidate))

    measured.sort(key=lambda pair: pair[0])
    return measured


def not_ordered_yet_suppliers(business_id) -> List:
    """Visible suppliers with stock that this shop has never bought
    from, the ones they already know first.

    THE TRUST IS DONE FOR A CONNECTED SUPPLIER and only the first order
    is missing, which makes them the cheapest win on the rail. Strangers
    follow, alphabetically -- a deliberate non-ranking, because nothing
    in the shop's own data separates two suppliers they have never used.

    THE RAIL THIS FEEDS IS THE ONE THAT IS TIE-BREAKABLE (V2_17 Q5): it
    prints no distance and no score, so its order is not a claim the
    reader can check. Nothing breaks ties by tier yet.
    """
    from src.domains.network.community.business.queries import (
        visible_suppliers_with_stock,
    )
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    candidates = visible_suppliers_with_stock()
    if not candidates:
        return []

    traded_with = set(
        StockOrderRepository.order_dates_by_counterparty(business_id=business_id).keys()
    )
    connected = connected_supplier_ids(business_id)

    untried = [p for p in candidates if str(p.id) not in traded_with]
    untried.sort(key=lambda p: (str(p.id) not in connected, p.business_name or ""))
    return untried


def paginate(items: List, *, limit: int, offset: int) -> dict:
    """One page, and an honest answer about whether there is another.

    hasMore IS LEN-BASED, not a COUNT(*). Every gather above already
    holds the full ranked set in memory -- they have to, to rank it --
    so the total is free here and a second query would be waste.
    """
    limit = max(1, min(limit, PAGE_SIZE))
    offset = max(0, offset)
    page = items[offset : offset + limit]
    return {
        "items": page,
        "hasMore": (offset + len(page)) < len(items),
        "total": len(items),
    }
