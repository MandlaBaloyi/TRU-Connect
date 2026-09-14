"""
The business's Community feed, section by section.

FOR THE BUSINESS, COMMUNITY IS A MARKET (V2_04 2.1) -- the mirror of
supplier_sections.py, which builds the same tab as a DEMAND SIGNAL for
the other role.

THE UI ALREADY EXISTS AND IS GOOD. This does not get to redesign it:
every shape below is what the app's own components already render from
mockCommunityFeed, so switching the seam from mock to HTTP changes no
screen. The section TYPES are the contract (V2_04 Part 1) -- the server
chooses which sections exist and in what order, the client renders what
it is handed and skips types it does not know.

TWO RULES THAT APPLY TO EVERY BUILDER HERE:

  THE CURTAIN. Every supplier reachable from this feed goes through
  verification.visibility -- an UNVERIFIED supplier is not findable, and
  a discovery rail is exactly where a bypass would hide. There is an
  architecture test that fails the build if this file reaches a supplier
  through the ungated lookup.

  A THIN RAIL IS WORSE THAN NO RAIL. MIN_ITEMS_PER_RAIL, stated in the
  app's own types.ts and enforced here too so a two-item rail cannot
  arrive from either side. Builders return None rather than a short
  list, for the same reason the supplier feed does: a zero card is worse
  than no card.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.network.community.business.cards import (
    feed_products,
    feed_suppliers,
    nearest_subtitle,
)
from src.domains.network.community.business.queries import (
    connected_supplier_ids,
    connected_supplier_profiles,
    visible_offers,
    visible_suppliers_with_stock,
)
from src.shared.algorithms import distance

#: A rail with almost nothing in it looks worse than no rail at all.
#: Mirrors MIN_ITEMS_PER_RAIL in the app's community/types.ts.
MIN_ITEMS_PER_RAIL = 3

#: Avatars are a row, not a rail -- two faces you recognise is still
#: useful where two products is not.
MIN_AVATARS = 1


# ---------------------------------------------------------------------------
# Category chips
# ---------------------------------------------------------------------------

def category_chips() -> dict:
    """The taxonomy, as chips that filter for real.

    THE ONE SECTION THAT IS NEVER EMPTY and never personal -- it is the
    same for every business, which is why it takes no arguments and
    needs no minimum.

    ICON NAMES COME FROM HERE, per the feed contract: a category added
    to the enum gets an icon on phones that have not been updated. The
    app keeps its own map as a fallback AND as a compile-time check that
    nobody forgot one -- see CATEGORY_DISPLAY's own comment.
    """
    from src.domains.catalogue.products.models.taxonomy import CATEGORY_DISPLAY, ProductCategory

    return {
        "id": "categories",
        "type": "CATEGORY_CHIPS",
        "categories": [
            {"value": category.value, "label": label, "icon": icon}
            for category in ProductCategory
            for label, icon in [CATEGORY_DISPLAY[category]]
        ],
    }


# ---------------------------------------------------------------------------
# Buy it again
# ---------------------------------------------------------------------------

def buy_it_again(business_id, limit: int = 12) -> Optional[dict]:
    """THE HIGHEST-VALUE RAIL IN THE APP (V2_04 2.2), and the cheapest
    to compute: this business's own order history.

    A spaza owner restocking buys the same handful of things every week
    and today has to re-find each one by scrolling a category. Ordering
    is per-BUSINESS, so this is genuinely personal history rather than a
    popularity list wearing its clothes.

    EMPTY FOR A NEW USER, AND THAT IS CORRECT -- it fills on order two.
    """
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    product_ids = StockOrderRepository.previously_ordered_product_ids_for_business(
        business_id, limit=limit * 2
    )
    if not product_ids:
        return None

    products = visible_offers(product_ids)
    if len(products) < MIN_ITEMS_PER_RAIL:
        return None

    return {
        "id": "buy-it-again",
        "type": "PRODUCT_RAIL",
        "title": "Buy it again",
        "subtitle": "From your last orders",
        "products": feed_products(products[:limit]),
    }


# ---------------------------------------------------------------------------
# Tell us what you buy  --  the only thing that asks for a declaration
# ---------------------------------------------------------------------------

def tell_us_what_you_buy(business_id) -> Optional[dict]:
    """Ask a shop what it buys, in the feed, at the moment it pays.

    WITHOUT THIS, PHASE 0 IS INERT. The demand engine is fed by a form,
    and nothing anywhere asked anybody to fill it in -- so an engine
    that turns a declaration into a better feed would sit waiting for a
    declaration nobody was invited to make.

    THE RULE THAT KEEPS IT HONEST (Book Three Part 9):

        ONLY ASK FOR WHAT WILL VISIBLY CHANGE THE NEXT SCREEN, AND SAY
        EXACTLY WHAT IT WILL CHANGE.

        GOOD  "Tell us what you buy and we will show you stock for it."
              -- true, specific, and the feed measurably changes.
        BAD   "Complete your profile!" with a progress ring -- a chore
              with no stated benefit, which is the pattern every app
              uses and every user has learned to dismiss.

    SO IT ASKS FOR ONE THING ONLY, and deliberately not for restock
    rhythm or spend band even though the engine reads both. Nothing
    VISIBLE uses those yet -- cadence feeds no section in Phase 0 -- and
    asking for them now would break the rule above in the first week it
    existed. They get asked when something uses them.

    IT DISAPPEARS THE MOMENT IT IS ANSWERED, and it is skippable
    forever: a shop that never answers gets a worse feed, never a
    blocked one.

    NO NEW CLIENT CODE. PROMO is already in the feed contract and the
    app already renders it -- which is the section-types-as-contract
    property doing exactly what V2_04 Part 1 promised.
    """
    from src.domains.business.demand.services import needs_service

    if needs_service.needs_for(business_id).is_known:
        return None

    return {
        "id": "tell-us-what-you-buy",
        "type": "PROMO",
        "promo": {
            "title": "What stock do you buy?",
            "body": "Tell us and we will show you stock for your shop, from suppliers near you.",
            "imageUrl": None,
            # Must start with /business/ -- PromoCard refuses anything
            # else rather than navigating somewhere a server told it to.
            "href": "/business/my-business/trading-details",
        },
    }


# ---------------------------------------------------------------------------
# Stock for what you buy  --  THE DEMAND ENGINE'S FIRST CONSUMER
# ---------------------------------------------------------------------------

#: No single supplier may own this rail. A wholesaler with four hundred
#: products would otherwise fill it entirely -- their catalogue is
#: simply bigger, and "more matches" is not "better for this shop".
#:
#: Coverage is still rewarded: below the cap, whoever stocks more of
#: what this shop buys appears more. Above it the rail makes room. See
#: docs/v2/V2_15 Book Two 7.4.
MAX_CARDS_PER_SUPPLIER = 3


def stock_for_what_you_buy(business_id, limit: int = 12) -> Optional[dict]:
    """Products in the categories this shop SAID it buys.

    THE FIRST THING THAT READS THE DEMAND ENGINE, and the whole argument
    for asking the questions at all: a shop that fills in the form gets
    a better feed THE SAME DAY, before it has placed a single order.

    Without it, a new business waits months of order history before the
    feed knows anything about them -- which is the cold-start hole every
    recommender falls into, and the reason declaration earns its place
    (Book Three Part 8).

    IT ASKS THE ENGINE, NOT THE PROFILE. needs_service is the only
    module the feed may call, so when the model gains an observed layer
    and a nightly rebuild, this source does not change at all.

    THE SUBTITLE SAYS WHY, DELIBERATELY. "Based on what you told us you
    buy" is the reason string V2_15 Book Two Part 3 requires -- it
    explains the rail, and it makes answering the next question feel
    worth doing.
    """
    from src.domains.business.demand.services import needs_service
    from src.domains.catalogue.discovery.services import browse_service

    needs = needs_service.needs_for(business_id)
    if not needs.is_known:
        # Nothing declared. NOT an empty rail -- a shop that has told us
        # nothing should see the platform-wide sections instead, not a
        # heading with nothing under it.
        return None

    result = browse_service.browse_category(
        business_id=business_id,
        categories=needs.category_values,
        # Over-fetch, because the supplier cap below removes cards and a
        # thin rail is worse than none.
        limit=limit * 3,
    )

    products = _cap_per_supplier(result.get("products") or [], MAX_CARDS_PER_SUPPLIER)
    if len(products) < MIN_ITEMS_PER_RAIL:
        return None

    return {
        "id": "stock-for-you",
        "type": "PRODUCT_RAIL",
        "title": "Stock for your shop",
        "subtitle": "Based on what you told us you buy",
        "products": products[:limit],
    }


def _cap_per_supplier(products: List[dict], cap: int) -> List[dict]:
    """Keep the rail a MARKET rather than one wholesaler's shelf.

    ORDER IS PRESERVED, so whatever ranking produced the list survives;
    this only removes a supplier's fourth, fifth and fortieth card.
    """
    seen: dict = {}
    kept = []
    for product in products:
        supplier_id = product.get("supplierId")
        count = seen.get(supplier_id, 0)
        if count >= cap:
            continue
        seen[supplier_id] = count + 1
        kept.append(product)
    return kept


# ---------------------------------------------------------------------------
# Your suppliers
# ---------------------------------------------------------------------------

def your_suppliers(business_id) -> Optional[dict]:
    """Existing connections as a row of avatars -- the fastest path back
    to a shopfront they already trust."""
    profiles = connected_supplier_profiles(business_id)
    if len(profiles) < MIN_AVATARS:
        return None

    return {
        "id": "your-suppliers",
        "type": "SUPPLIER_AVATARS",
        "title": "Your suppliers",
        "suppliers": feed_suppliers(profiles),
    }


# ---------------------------------------------------------------------------
# Suppliers you haven't ordered from
# ---------------------------------------------------------------------------

def not_ordered_from_yet(business_id, limit: int = 10) -> Optional[dict]:
    """Visible suppliers this shop has never ordered from -- CONNECTED
    OR NOT.

    IT USED TO BE CONNECTION-ONLY, and that was the smaller half of a
    real idea. A connection that stalled after the handshake and a
    supplier they have never met are the SAME opportunity from the
    platform's point of view: somebody with stock, in reach, that this
    shop has never bought from. Restricting it to connections meant a
    new business -- who has none -- saw nothing at all.

    It was also the old model leaking back in. V2_00 2.3 removed the
    connection requirement so that discovery could exist; rebuilding it
    inside a discovery rail put it straight back.

    DELIBERATELY NOT FRAMED AS A FAILURE. The subtitle states a fact.
    Anything scolding would be the platform telling a shopkeeper off for
    how they run their shop.
    """
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    candidates = visible_suppliers_with_stock()
    if not candidates:
        return None

    traded_with = set(
        StockOrderRepository.order_dates_by_counterparty(business_id=business_id).keys()
    )
    connected = connected_supplier_ids(business_id)

    untried = [p for p in candidates if str(p.id) not in traded_with]
    if len(untried) < MIN_ITEMS_PER_RAIL:
        return None

    # A SUPPLIER THEY ALREADY KNOW COMES FIRST. The trust is done; only
    # the first order is missing, which makes it the cheapest one to
    # win. Strangers follow.
    untried.sort(key=lambda p: (str(p.id) not in connected, p.business_name or ""))

    return {
        "id": "not-ordered-yet",
        "type": "SUPPLIER_RAIL",
        "title": "Suppliers you haven't ordered from",
        "subtitle": "In reach, and new to you",
        "suppliers": feed_suppliers(untried[:limit], connected_ids=connected),
    }


# ---------------------------------------------------------------------------
# Collect near you
# ---------------------------------------------------------------------------

def collect_near_you(business_id, limit: int = 10) -> Optional[dict]:
    """Verified suppliers close enough to collect from.

    IT USED TO EXCLUDE CONNECTED SUPPLIERS and that was wrong here.
    The reasoning -- a discovery rail containing your own suppliers is a
    bug -- is right for a rail called "new near you" and wrong for one
    called "COLLECT near you": proximity is useful whoever they are, and
    the wholesaler you already buy from being the nearest is
    information, not noise. They are badged instead of hidden.

    NO LOCATION, NO RAIL. Without the business's own coordinates there
    is no "near", and an unsorted list of every supplier would be worse
    than nothing because it would look like a recommendation.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter
    from src.extensions import db

    profile = BusinessProfileRepository.get_for_business(business_id)
    if profile is None or profile.latitude is None or profile.longitude is None:
        return None

    connected = connected_supplier_ids(business_id)

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

    measured = []
    for candidate in candidates:
        km = distance.km_between(
            profile.latitude,
            profile.longitude,
            candidate.collection_latitude,
            candidate.collection_longitude,
        )
        if km is None:
            continue
        measured.append((km, candidate))

    if len(measured) < MIN_ITEMS_PER_RAIL:
        return None

    measured.sort(key=lambda pair: pair[0])
    nearest = measured[:limit]

    return {
        "id": "collect-near-you",
        "type": "SUPPLIER_RAIL",
        "title": "Collect near you",
        "subtitle": nearest_subtitle(profile),
        "suppliers": feed_suppliers(
            [p for _, p in nearest],
            distances={p.id: round(km, 1) for km, p in nearest},
            connected_ids=connected,
        ),
    }
