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

    products = _visible_offers(product_ids)
    if len(products) < MIN_ITEMS_PER_RAIL:
        return None

    return {
        "id": "buy-it-again",
        "type": "PRODUCT_RAIL",
        "title": "Buy it again",
        "subtitle": "From your last orders",
        "products": _feed_products(products[:limit]),
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
    profiles = _connected_supplier_profiles(business_id)
    if len(profiles) < MIN_AVATARS:
        return None

    return {
        "id": "your-suppliers",
        "type": "SUPPLIER_AVATARS",
        "title": "Your suppliers",
        "suppliers": _feed_suppliers(profiles),
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

    candidates = _visible_suppliers_with_stock()
    if not candidates:
        return None

    traded_with = set(
        StockOrderRepository.order_dates_by_counterparty(business_id=business_id).keys()
    )
    connected = _connected_supplier_ids(business_id)

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
        "suppliers": _feed_suppliers(untried[:limit], connected_ids=connected),
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

    connected = _connected_supplier_ids(business_id)

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
        "subtitle": _nearest_subtitle(profile),
        "suppliers": _feed_suppliers(
            [p for _, p in nearest],
            distances={p.id: round(km, 1) for km, p in nearest},
            connected_ids=connected,
        ),
    }


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _connected_supplier_ids(business_id) -> set:
    """Just the ids, for badging and ordering -- no profile loads.

    Separate from _connected_supplier_profiles because most callers only
    need to ask "is this one of mine?", and loading a profile per
    connection to answer a boolean is the N+1 this file has already had
    removed once.
    """
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )

    if business_id is None:
        return set()
    return {
        str(r.supplier_profile_id)
        for r in ConnectionRequestRepository.list_active_for_business(business_id)
    }


def _visible_suppliers_with_stock(limit: int = 200) -> List:
    """Visible suppliers that actually have something to sell.

    A SUPPLIER WITH AN EMPTY SHOPFRONT IS NOT AN OPPORTUNITY. Putting
    one in a discovery rail sends a shopkeeper to a blank screen, which
    teaches them the rail is not worth tapping -- and the ordering gate
    refuses them anyway ("there is nothing to order from an empty
    catalogue"), so the card could never have become an order.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter
    from src.extensions import db

    return (
        db.session.query(SupplierProfile)
        .join(SupplierOffer, SupplierOffer.supplier_profile_id == SupplierProfile.id)
        .filter(
            visible_filter(),
            SupplierProfile.is_deleted.is_(False),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
        )
        .distinct()
        .limit(limit)
        .all()
    )


def _connected_supplier_profiles(business_id) -> List:
    """Active connections, CURTAINED.

    A supplier whose verification was revoked stops being discoverable,
    but an established connection and its order history stay -- so this
    filters the DISCOVERY surfaces without pretending the trade never
    happened. That distinction is V2_12's, not this file's.
    """
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )
    profiles = []
    for request in ConnectionRequestRepository.list_active_for_business(business_id):
        # get_visible_by_id, NOT get_by_id: the gate belongs in the
        # lookup rather than in a filter after it, so there is no window
        # in which an unverified profile exists in a local variable on a
        # business-facing path. The architecture test enforces exactly
        # this and caught the first version of this function.
        profile = SupplierProfileRepository.get_visible_by_id(request.supplier_profile_id)
        if profile is not None:
            profiles.append(profile)
    return profiles


def _visible_offers(product_ids: List[UUID]) -> List:
    """Load supplier offers by id, keeping only those whose supplier is
    still visible and whose listing is still live.

    ORDER IS PRESERVED from product_ids, which arrived most-recently-
    ordered first -- a set lookup would silently resort the rail into
    whatever order the database felt like returning.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
    from src.domains.verification.visibility import visible_filter
    from src.extensions import db

    if not product_ids:
        return []

    rows = (
        db.session.query(SupplierOffer, SupplierProfile.business_name)
        .join(SupplierProfile, SupplierProfile.id == SupplierOffer.supplier_profile_id)
        .filter(
            SupplierOffer.id.in_(product_ids),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
            visible_filter(),
        )
        .all()
    )
    # THE SUPPLIER NAME COMES OUT OF THIS QUERY, not a lookup per card.
    # The first version fetched each supplier separately to name the
    # card, which was both a second read and an UNGATED one -- the
    # curtain test refused it, correctly. Joining it here is cheaper and
    # cannot drift from the visibility filter directly above.
    by_id = {offer.id: (offer, name) for offer, name in rows}
    return [by_id[pid] for pid in product_ids if pid in by_id]


def _feed_products(pairs: List) -> List[dict]:
    """SupplierOffer rows in the shape the app's product cards render.

    Reuses build_catalog_product_dicts for the parts that are easy to
    get subtly wrong -- batched inventory rather than a query per
    product, and APPROVED-only media -- then maps to the feed's own
    flatter shape, which carries the supplier on every card because a
    feed rail mixes suppliers where a shopfront never does.
    """
    from src.domains.network.connections.services.storefront.product_dto import (
        build_catalog_product_dicts,
    )

    offers = [pair[0] for pair in pairs]
    enriched = build_catalog_product_dicts(offers)
    feed_products = []

    for (offer, supplier_name), dto in zip(pairs, enriched):
        supplier_id = offer.supplier_profile_id
        images = dto.get("images") or []
        feed_products.append(
            {
                "id": dto["id"],
                "supplierId": str(supplier_id),
                "supplierName": supplier_name,
                "name": dto["name"],
                # ONE image, not the gallery: a rail card shows a
                # thumbnail, and shipping four URLs per card to render
                # one is bandwidth a spaza shop pays for.
                "imageUrl": (images[0].get("url") if isinstance(images[0], dict) else images[0])
                if images
                else None,
                "priceCents": dto["priceCents"],
                "compareAtPriceCents": dto["compareAtPriceCents"],
                "unitLabel": _unit_label(dto),
                "inStock": dto["inStock"],
            }
        )
    return feed_products


def _unit_label(dto: dict) -> Optional[str]:
    """"each", "case of 12", "bag of 10kg".

    BUILT SERVER-SIDE because the feed contract says so, and because the
    three columns it is built from (selling unit, quantity, measure) are
    exactly the ones that were never sent to a business before -- a pack
    of 6 and a pack of 24 looked identical at the same price.
    """
    unit = (dto.get("sellingUnit") or "").lower()
    quantity = dto.get("unitQuantity")
    measure = (dto.get("unitMeasure") or "").lower() if dto.get("unitMeasure") else None

    if not unit:
        return None
    if unit == "each" or not quantity:
        return unit
    if measure:
        return f"{unit} of {quantity}{measure}"
    return f"{unit} of {quantity}"


def _feed_supplier(
    profile,
    distance_km: Optional[float] = None,
    last_active_at=None,
    is_connected: bool = False,
) -> dict:
    """The supplier card shape, ungated brand assets only.

    NO STREET ADDRESS, ever -- `location` is suburb or city, the same
    rule the search results follow. A discovery rail is seen by people
    with no relationship to this supplier.
    """
    return {
        "id": str(profile.id),
        "businessName": profile.business_name,
        "businessImageUrl": profile.business_image_url,
        "coverImageUrl": profile.cover_image_url,
        "category": profile.category,
        "location": profile.location,
        "verificationStatus": (
            profile.verification_status.value if profile.verification_status else None
        ),
        "offersDelivery": profile.offers_delivery,
        "minimumOrderCents": profile.minimum_order_cents,
        "distanceKm": distance_km,
        # THE CARD ALREADY HAD A BADGE FOR THIS and nothing ever set
        # it. Now that discovery rails show connected suppliers
        # rather than hiding them, it is the field that tells a shop
        # which of these they already deal with.
        "isConnected": is_connected,
        # FROM THE SUPPLIER'S USER ROW, not the profile -- the heartbeat
        # lives on auth.users -- and only when they have chosen to show
        # it. Passed in rather than looked up here so the caller can
        # batch one query for the whole rail instead of one per card.
        "lastActiveAt": last_active_at.isoformat() if last_active_at else None,
    }


def _feed_suppliers(
    profiles: List,
    distances: Optional[dict] = None,
    connected_ids: Optional[set] = None,
) -> List[dict]:
    """Every supplier card in a rail, with the activity lookup batched."""
    seen = _last_active_map(profiles)
    return [
        _feed_supplier(
            p,
            distance_km=(distances or {}).get(p.id),
            last_active_at=seen.get(p.id),
            is_connected=str(p.id) in (connected_ids or set()),
        )
        for p in profiles
    ]


def _last_active_map(profiles: List) -> dict:
    """{supplier_profile_id: last_active_at or None}, in ONE query.

    Gated by the supplier's own show_last_active, the same rule
    discovery_service applies -- a supplier who turned the indicator off
    has turned it off everywhere, not just on their profile screen.
    """
    from src.domains.auth.models.user import User
    from src.extensions import db

    wanted = {p.supplier_id: p.id for p in profiles if p.show_last_active}
    if not wanted:
        return {}

    rows = db.session.query(User.id, User.last_active_at).filter(User.id.in_(wanted.keys())).all()
    return {wanted[user_id]: seen for user_id, seen in rows}


def _nearest_subtitle(profile) -> Optional[str]:
    """"Closest to Soweto" -- the business's own suburb, not a distance.

    A number here would be the distance to the FIRST card, which stops
    being true as soon as the reader scrolls.
    """
    where = profile.city_or_town
    return f"Closest to {where}" if where else None
