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
from src.domains.network.community.placement import tie_break
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


def left_off_cards(business_id, *, limit: int = PAGE_SIZE) -> List[dict]:
    """Products this shop opened and never ordered, most-tapped first.

    THE PAGED VERSION OF THE RAIL, and the reason the rail needed an
    arrow at all: a shop that browses fifty products cannot reach the
    fiftieth by scrolling a twelve-card shelf sideways. The rail is a
    preview; this is the list.

    THE SAME RULES AS THE RAIL, deliberately, so the screen behind the
    arrow cannot disagree with the row that opened it -- taps rather
    than deliveries, the ordered ones excluded, and the same fourteen
    day window. Only the length differs, which is the contract every
    other see-all here follows.

    NO PER-SUPPLIER CEILING AT THIS LENGTH. The cap on the rail exists
    because twelve cards are a recommendation and one wholesaler must
    not own them. A full list is not a recommendation -- it is the
    shop's own browsing history, and hiding part of it because one
    supplier happens to sell what they were looking at would be the
    screen refusing to answer the question it was opened to answer.
    """
    from src.domains.business.demand.signals.considered import CONSIDERED_WINDOW_DAYS
    from src.domains.network.impressions.repositories.impression_repository import (
        ImpressionRepository,
    )
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    already_ordered = StockOrderRepository.previously_ordered_product_ids_for_business(
        business_id, limit=200
    )
    since = (utcnow() - timedelta(days=CONSIDERED_WINDOW_DAYS)).date()
    product_ids = ImpressionRepository.tapped_not_ordered(
        business_id, since=since, exclude=already_ordered, limit=limit * 2
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

    # ---------------------------------------------------------------
    # RELEVANCE IS A FILTER HERE AND NEVER AN ORDER, and that is not a
    # preference -- tie_break.py settles it:
    #
    #     A rail may be tie-broken only if it does not DISPLAY the fact
    #     it is ordered by.
    #
    # This rail prints "1.2 km" on every card. Reordering it puts 2.0km
    # above 1.2km in front of a reader who can see both numbers; they
    # conclude either that the app is broken or that the order was
    # bought, and the second conclusion would be correct. So the list
    # stays strictly distance-ordered and every printed number stays
    # true. What relevance may do is decide who is ON it.
    #
    # THE PRECEDENT IS THE RAIL'S OWN: it already drops anyone beyond
    # MAX_COLLECTION_KM "rather than shown as the best of a bad lot".
    # A wholesaler four hundred metres away who sells nothing this shop
    # buys is the same kind of card -- near, and no use.
    #
    # TWO VALVES, BOTH LOAD-BEARING:
    #
    #   NO SIGNAL, NO FILTER. A shop that has declared nothing and
    #   ordered nothing sees everyone, exactly as before. That shop is
    #   precisely who a discovery rail is for, and a relevance filter
    #   with nothing to match on would empty it.
    #
    #   NEVER SHRINK IT BELOW A RAIL. If filtering leaves fewer than
    #   MIN_ITEMS_PER_RAIL the unfiltered list is kept. A rail that
    #   vanishes teaches a shopkeeper that nobody is near them, which
    #   is a worse lie than a loose card.
    from src.domains.business.demand.services import needs_service
    from src.domains.network.community.business.sections import MIN_ITEMS_PER_RAIL
    from src.domains.network.community.placement import relevance as relevance_rules

    needs = needs_service.needs_for(business_id)
    if not needs.is_known:
        return measured

    wanted = set(needs.category_values)
    carried = relevance_rules.categories_by_supplier([p.id for _, p in measured])
    relevant = [
        pair
        for pair in measured
        if relevance_rules.sells_anything_needed(carried.get(pair[1].id), wanted)
    ]

    if len(relevant) < MIN_ITEMS_PER_RAIL:
        return measured
    return relevant


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

    # WHAT THIS SHOP ACTUALLY BUYS -- a question this rail never asked.
    # The engine answers in categories and weights and never names a
    # supplier; the match itself happens in placement/relevance.py, on
    # this side of the supplier-blind wall.
    #
    # None WHEN NOTHING IS KNOWN, never a map of zeroes. A shop that has
    # declared nothing and ordered nothing gets exactly the old
    # ordering -- and that shop is the one this rail exists for.
    from src.domains.business.demand.services import needs_service
    from src.domains.network.community.placement import relevance as relevance_rules

    needs = needs_service.needs_for(business_id)
    scores = (
        relevance_rules.rank(untried, weights=needs.weight_by_category)
        if needs.is_known
        else None
    )

    # THE ONE RAIL WHERE A PLAN MAY ORDER THE EQUALS. It prints no
    # distance and no score, so its order is not a claim the reader can
    # check -- unlike "collect near you", which prints the very number
    # it is sorted by. Whether they already KNOW a supplier still ranks
    # first, at every tier, for any money.
    return tie_break.order_untried_suppliers(
        untried, connected_ids=connected, relevance=scores
    )


SEE_ALL_SORTS = ("relevance", "price_asc", "price_desc", "name")


def present(
    cards: List[dict],
    *,
    search: Optional[str] = None,
    sort: str = "relevance",
    supplier: Optional[str] = None,
    limit: int,
    offset: int,
) -> dict:
    """A see-all page: narrowed, ordered, counted, with its facets.

    THE SAME CONTROLS THE CATEGORY BROWSE HAS, because these screens
    have the same problem. "Reorder what you need" for a shop with a
    hundred lines is the browse's thousand-product scroll in miniature,
    and the answer is the same: let them narrow rather than asking them
    to scroll.

    IN MEMORY, AND THAT IS CORRECT HERE. The browse filters in SQL
    because it is looking at the whole market; every gather feeding this
    function is already bounded and already fully materialised -- a
    shop's own order history, its own taps, the rising set. They have to
    be, to rank at all. Pushing these filters into SQL would mean four
    more query paths for lists that are small by construction.

    "relevance" IS THE DEFAULT AND MEANS "LEAVE IT ALONE". Each of these
    lists arrives in an order that took real work to produce -- most
    recently ordered, most tapped, fastest rising -- and that order IS
    the rail's argument for existing. A see-all that silently
    alphabetised it would throw away the reason the reader tapped
    through.

    THE FACETS ARE COUNTED BEFORE PAGING AND AFTER FILTERING, so a chip
    promises what tapping it returns -- the same rule the browse chips
    follow, and the bug that taught it.
    """
    narrowed = cards

    if search:
        needle = search.strip().lower()
        if needle:
            # NAME AND SUPPLIER BOTH, because a shopkeeper looking for
            # "MacMan" is asking a real question about this list and
            # would otherwise get nothing.
            narrowed = [
                card
                for card in narrowed
                if needle in (card.get("name") or "").lower()
                or needle in (card.get("supplierName") or "").lower()
            ]

    # THE FACETS ARE COUNTED BEFORE THE SUPPLIER FILTER IS APPLIED, and
    # that ordering is the whole point. Counting after it leaves exactly
    # ONE chip standing -- the one you just tapped -- so the row
    # collapses and there is no way back to the others without a filter
    # nobody can see. Tapping Seshego should narrow the PRODUCTS and
    # leave the other wholesalers on screen as the alternatives they
    # are.
    #
    # SEARCH IS APPLIED FIRST AND DELIBERATELY. It narrows what the
    # question is ABOUT, so the chips should answer "who sells the
    # Colgate in this list"; the supplier filter narrows the ANSWER, so
    # the chips must survive it. The browse's kind chips follow the same
    # rule for the same reason.
    suppliers: dict = {}
    for card in narrowed:
        supplier_id = card.get("supplierId")
        if not supplier_id:
            continue
        entry = suppliers.setdefault(
            supplier_id, {"id": supplier_id, "name": card.get("supplierName"), "count": 0}
        )
        entry["count"] += 1

    if supplier:
        narrowed = [card for card in narrowed if card.get("supplierId") == supplier]

    if sort == "price_asc":
        narrowed = sorted(narrowed, key=lambda c: c.get("priceCents") or 0)
    elif sort == "price_desc":
        narrowed = sorted(narrowed, key=lambda c: c.get("priceCents") or 0, reverse=True)
    elif sort == "name":
        narrowed = sorted(narrowed, key=lambda c: (c.get("name") or "").lower())

    page = paginate(narrowed, limit=limit, offset=offset)
    result = {
        "products": page["items"],
        "hasMore": page["hasMore"],
        "total": page["total"],
    }
    # FACETS ON THE FIRST PAGE ONLY, matching the browse: they do not
    # change as you scroll, and shipping them on every page is bytes a
    # spaza shop pays for.
    if offset == 0:
        result["suppliers"] = sorted(
            suppliers.values(), key=lambda s: (-s["count"], (s["name"] or "").lower())
        )[:12]
    return result


def present_suppliers(
    rows: List,
    *,
    search=None,
    kind=None,
    limit: int,
    offset: int,
) -> dict:
    """A supplier see-all page: narrowed, counted, with its kind facets.

    TAKES EITHER SHAPE. collect-near-you carries (km, profile) tuples
    because it prints the distance; not-ordered-yet carries bare
    profiles. Normalising here means one narrowing rule rather than two
    that drift apart.

    NO SORT CONTROL, AND THAT IS DELIBERATE. collect_near_you is
    "strictly distance-ordered, at every tier, forever" -- it is the
    only surface that PRINTS the number it is sorted by, so a reorder
    is a contradiction the reader is holding (V2_17 Q5). Offering A-Z
    there would let somebody produce a list headed "closest to
    Mankweng" that is not in distance order. NARROWING does not have
    that problem: filtering to wholesalers leaves the survivors in
    distance order, and the heading stays true.

    AND THE TWO SCREENS GET THE SAME CONTROLS, because a control that
    exists on one discovery screen and not the other is a control
    nobody learns.

    KIND IS THE AXIS, matching the category browse and Explore -- the
    same small closed set, and on a discovery screen it is the question
    worth asking: a cash-and-carry and a manufacturer are different
    propositions for the same shop.
    """
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierKind

    def profile_of(row):
        return row[1] if isinstance(row, tuple) else row

    def kind_of(row):
        value = profile_of(row).supplier_kind
        return getattr(value, "value", value)

    narrowed = rows

    if search:
        needle = search.strip().lower()
        if needle:
            narrowed = [
                row
                for row in narrowed
                if needle in (profile_of(row).business_name or "").lower()
            ]

    # COUNTED BEFORE THE KIND FILTER IS APPLIED. Counting after it
    # leaves exactly one chip standing -- the one just tapped -- and the
    # row collapses with no way back to a filter nobody can see. Same
    # rule the browse and the product see-alls follow, and the same bug
    # that taught it.
    counts = {}
    for row in narrowed:
        value = kind_of(row)
        if not value or value == SupplierKind.UNSPECIFIED.value:
            continue
        counts[value] = counts.get(value, 0) + 1

    if kind:
        narrowed = [row for row in narrowed if kind_of(row) == kind]

    page = paginate(narrowed, limit=limit, offset=offset)
    result = {"items": page["items"], "hasMore": page["hasMore"], "total": page["total"]}
    if offset == 0:
        # A STABLE ORDER, from the enum rather than from a dict, so the
        # chips do not move between visits.
        result["kinds"] = [
            {"id": k.value, "name": k.value, "count": counts[k.value]}
            for k in SupplierKind
            if k.value in counts
        ]
    return result


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
