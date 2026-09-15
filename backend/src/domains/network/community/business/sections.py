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
from src.domains.network.community.algorithms import interleave

#: A rail with almost nothing in it looks worse than no rail at all.
#: Mirrors MIN_ITEMS_PER_RAIL in the app's community/types.ts.
MIN_ITEMS_PER_RAIL = 3

#: HOW MANY CARDS EACH RAIL SHOWS BEFORE THE ARROW (V2_17 Part 3.1).
#:
#: A RAIL IS A PREVIEW, NOT A CONTAINER, and until now it was neither:
#: it scrolled right for as long as the query happened to return, which
#: looks fine with four suppliers and will not. Without a cap AND a way
#: out, a shop with sixty previously-ordered products silently loses
#: forty-eight of them -- the cap alone is just truncation.
#:
#: THE NUMBERS DIFFER BY WHAT THE RAIL IS FOR. Product rails carry a
#: dozen because scanning stock is quick; "collect near you" carries
#: five because choosing between SUPPLIERS is a slower, heavier decision
#: and a long row of them is a chore rather than a choice.
RAIL_LIMITS = {
    "buy-it-again": 12,
    "moving-fast": 10,
    "stock-for-you": 12,
    "your-suppliers": 12,
    "collect-near-you": 5,
    "not-ordered-yet": 10,
    "invited-suppliers": 10,
}

#: Where the arrow goes. THE APP OWNS THESE PATHS and the server only
#: names them, which is the same contract the feed already has for
#: section TYPES: the client renders what it recognises and ignores what
#: it does not, so a new destination ships server-side.
SEE_ALL_HREFS = {
    "buy-it-again": "/business/community/buy-it-again",
    "moving-fast": "/business/community/moving-fast",
    "stock-for-you": "/business/community/stock-for-you",
    "collect-near-you": "/business/community/collect-near-you",
    "not-ordered-yet": "/business/community/not-ordered-yet",
    # NOT A NEW SCREEN. "Your suppliers" past the cap is My Connections,
    # which already exists and is already the right screen for the full
    # list -- building a second one would be two places to keep honest.
    "your-suppliers": "/business/my-connections",
}

#: Avatars are a row, not a rail -- two faces you recognise is still
#: useful where two products is not.
MIN_AVATARS = 1


# ---------------------------------------------------------------------------
# Category chips
# ---------------------------------------------------------------------------

def _rail_tail(rail_id: str, shown: int, available: int) -> dict:
    """hasMore and seeAllHref, or nothing at all.

    ABSENT RATHER THAN FALSE when everything fits. The app renders the
    arrow when it sees the key, so a rail that has nothing behind it
    says nothing -- and an arrow leading to a screen identical to the
    rail is a worse lie than no arrow.

    available IS "HOW MANY WE FOUND", not a COUNT(*). Every caller here
    already over-fetches past its own cap for other reasons, so the
    comparison is free; asking the database for a true total on every
    feed load would be six extra counts to render one chevron.
    """
    if available <= shown:
        return {}
    return {"hasMore": True, "seeAllHref": SEE_ALL_HREFS.get(rail_id)}


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
    from src.domains.network.community.services import feed_detail_service

    limit = RAIL_LIMITS["buy-it-again"]
    products = feed_detail_service.buy_it_again_cards(business_id, limit=limit * 2)
    if len(products) < MIN_ITEMS_PER_RAIL:
        return None

    # NO PER-SUPPLIER CEILING HERE, AND THAT IS DELIBERATE (V2_17 Q3).
    # This is the shop's own confirmed purchase history. If they buy
    # fifteen things from MacMan that is a fact about their trading, not
    # a wholesaler crowding a feed, and capping it would hide a shop's
    # own stock from itself. The anti-domination rule is a rule about
    # RECOMMENDATION; this rail only remembers.
    # tests/architecture/test_placement_boundaries.py holds that.
    return {
        "id": "buy-it-again",
        "type": "PRODUCT_RAIL",
        "title": "Buy it again",
        "subtitle": "From your last orders",
        "products": products[:limit],
        **_rail_tail("buy-it-again", min(limit, len(products)), len(products)),
    }


def moving_fast(business_id, limit: int = 12) -> Optional[dict]:
    """Products selling faster than they usually do -- in the categories
    THIS shop buys.

    NOT A BESTSELLER LIST, and the distinction is the whole reason it
    exists. A bestseller is a product that has always sold well, which a
    shopkeeper already knows about; this is a product selling faster
    than ITSELF. Maize meal before a long weekend, cooldrink in a
    heatwave, stationery in January. The judgement lives in
    algorithms/velocity.py, deliberately, where the numbers can be read
    as the guesses they are.

    IT ASKS THE DEMAND ENGINE FIRST. A spike in nappies means nothing to
    a shop that does not sell them, and an unfiltered version of this
    rail would be a platform leaderboard wearing a personal title --
    which is also how one wholesaler's volume would start deciding what
    everybody sees. Filtering to the shop's own categories keeps it
    personal AND keeps the anti-domination property the whole
    demand-first design is built on.

    TWO QUERIES, both windowed aggregates over the whole platform, and
    they do not grow with the number of products on the rail.
    """
    from src.domains.network.community.services import feed_detail_service

    limit = RAIL_LIMITS["moving-fast"]
    # THE GATHERING LIVES IN feed_detail_service so this rail and the
    # screen its arrow opens cannot rank differently -- a "see all" that
    # disagreed with the rail it came from is a bug the reader sees
    # immediately and no test ever would.
    all_cards = feed_detail_service.moving_fast_cards(business_id, limit=limit * 4)
    if len(all_cards) < MIN_ITEMS_PER_RAIL:
        return None
    # CAP, INTERLEAVE, THEN TRIM -- see algorithms/interleave.arrange.
    # A rail of one wholesaler's spike is that wholesaler's news, not
    # the market's.
    products = interleave.arrange(
        all_cards, absolute_cap=MAX_CARDS_PER_SUPPLIER, limit=limit
    )
    if len(products) < MIN_ITEMS_PER_RAIL:
        return None

    return {
        "id": "moving-fast",
        "type": "PRODUCT_RAIL",
        "title": "Moving fast right now",
        # THE REASON STRING, and it has to stay true like every other
        # one. It also has to sound like a person wrote it: "selling
        # quicker than usual in the last 7 days" was accurate and read
        # like a database talking.
        #
        # WHAT IT SAYS NOW IS LITERALLY WHAT THE ALGORITHM MEASURES --
        # the last 7 days against that product's own previous 28 --
        # which is why it can name a comparison rather than hiding
        # behind "usual". And it says WHO: other shops, which is the
        # part a shopkeeper actually trusts.
        "subtitle": "Shops are buying these faster than last month",
        "products": products,
        **_rail_tail("moving-fast", len(products), len(all_cards)),
    }


def invited_suppliers(business_id, limit: int = 10) -> Optional[dict]:
    """Suppliers who joined because THIS business invited them.

    THE ONE LOOP THE FEED NEVER CLOSED. Inviting a supplier is the most
    effort a shopkeeper can put into this platform -- they leave the
    app, message somebody they already trade with, and talk them into
    signing up. Until now the app said nothing afterwards. No "they
    joined", no "still waiting". The single most invested action a user
    can take had no reply, which is the surest way to make sure nobody
    does it twice.

    ONE CARD IS ENOUGH HERE, unlike every other rail on this screen.
    MIN_ITEMS_PER_RAIL exists because a discovery rail with two cards
    looks broken -- it implies a thin catalogue. This rail is not
    discovery: "Thabo Beverages joined because you invited them" is a
    complete thought on its own, and padding it would be the mistake.

    THE CURTAIN IS NOT RELAXED FOR IT. An invited supplier who has
    registered but not been verified does NOT appear -- they are hidden
    from buyers like any other unverified supplier (V2_15 Part 12: the
    curtain never relaxes, not for sponsorship, not for demo, not for a
    thin rail). The waiting count in the subtitle is a NUMBER, never a
    name, so nothing here tells a business that a particular email now
    has an account.

        WORTH A DECISION LATER, and flagged rather than taken here: a
        business that invited somebody arguably already knows they
        exist, so showing them pre-verification leaks nothing new to
        that reader. That is a real argument for a narrow exception --
        and a curtain exception is exactly the kind of thing that
        should be decided deliberately, not introduced by a feed rail.
    """
    from src.domains.network.connections.models.network_invitation import (
        InvitationStatus,
        InvitedRole,
    )
    from src.domains.network.connections.repositories.network_invitation_repository import (
        NetworkInvitationRepository,
    )
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )
    from src.domains.verification.visibility import is_visible_to_buyers

    invitations = NetworkInvitationRepository.list_sent_by(business_id, InvitedRole.SUPPLIER)
    if not invitations:
        return None

    waiting = sum(1 for i in invitations if i.status == InvitationStatus.PENDING)

    joined = []
    for invitation in invitations:
        if invitation.status == InvitationStatus.PENDING or not invitation.invited_user_id:
            continue
        profile = SupplierProfileRepository.get_by_supplier_id(invitation.invited_user_id)
        # THE GATE, and it is the sanctioned helper rather than a
        # verification_status comparison written out here -- the curtain
        # is defined in one module and the architecture test enforces
        # that (tests/architecture/test_verification_curtain.py).
        if profile is None or not is_visible_to_buyers(profile):
            continue
        joined.append(profile)

    if not joined:
        return None

    connected = connected_supplier_ids(business_id)

    return {
        "id": "invited-suppliers",
        "type": "SUPPLIER_RAIL",
        "title": "They joined because of you",
        "subtitle": _invitation_subtitle(waiting),
        "suppliers": feed_suppliers(
            joined[: RAIL_LIMITS["invited-suppliers"]], connected_ids=connected
        ),
        # No seeAllHref: there is no screen for this and there should
        # not be one. A shop that invited more than ten suppliers who
        # all joined is a case worth celebrating, not paginating.
        **_rail_tail(
            "invited-suppliers",
            min(RAIL_LIMITS["invited-suppliers"], len(joined)),
            len(joined),
        ),
    }


def _invitation_subtitle(waiting: int) -> Optional[str]:
    """A COUNT, NEVER A NAME. Saying "waiting on joe@example.com" would
    confirm to the reader that a particular address does or does not
    have an account, which is the supplier's business and not theirs --
    even though they supplied the address themselves."""
    if waiting <= 0:
        return "Suppliers you brought to TruConnect"
    if waiting == 1:
        return "1 more invitation still waiting"
    return f"{waiting} more invitations still waiting"


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
# MAX_COLLECTION_KM MOVED TO services/feed_detail_service.py, with the
# distance measuring it bounds. Two definitions of "near" -- one for the
# rail and one for the screen its arrow opens -- is precisely the drift
# that made moving the gathering worth doing. Imported from there by
# anything that needs the number.

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
    from src.domains.network.community.services import feed_detail_service

    needs = needs_service.needs_for(business_id)
    if not needs.is_known:
        # Nothing declared. NOT an empty rail -- a shop that has told us
        # nothing should see the platform-wide sections instead, not a
        # heading with nothing under it.
        return None

    limit = RAIL_LIMITS["stock-for-you"]
    # THE SAME CALL THE SCREEN BEHIND THE ARROW MAKES -- affordability
    # ordering, category weighting and all -- differing only in length.
    products = feed_detail_service.stock_for_you_cards(business_id, limit=limit * 3)
    available = len(products)
    products = interleave.arrange(
        products, absolute_cap=MAX_CARDS_PER_SUPPLIER, limit=limit
    )
    if len(products) < MIN_ITEMS_PER_RAIL:
        return None

    return {
        "id": "stock-for-you",
        "type": "PRODUCT_RAIL",
        "title": "Stock for your shop",
        "subtitle": _why_this_rail(needs),
        "products": products,
        **_rail_tail("stock-for-you", len(products), available),
    }


# _strongest_needs_first MOVED TO services/feed_detail_service.py, so
# the rail and the screen behind its arrow sort by the same weights
# rather than each holding a copy of the rule.


def _why_this_rail(needs) -> str:
    """The reason string, and it has to stay TRUE.

    "Based on what you told us you buy" was honest in Phase 0, when a
    declaration was all the engine had. It is now a lie to a shop whose
    needs were learned from its own orders -- and the one thing a
    self-explaining feed cannot afford is an explanation the reader
    knows is wrong. A shop that never filled the form and reads "what
    you told us" concludes the app is guessing.
    """
    sources = {n.source for n in needs.categories}
    if sources == {"declared"}:
        return "Based on what you told us you buy"
    if "declared" in sources or "both" in sources:
        return "Based on what you buy and what you told us"
    return "Based on what you buy"


# _cap_per_supplier MOVED TO algorithms/interleave.py, where it sits
# beside the run rule it is half of. Keeping a rail a market turned out
# to be two protections, not one -- how many cards a supplier may hold,
# and how many may sit next to each other -- and they were a file apart
# while being read as the same thing. Call interleave.arrange().


# ---------------------------------------------------------------------------
# Your suppliers
# ---------------------------------------------------------------------------

def your_suppliers(business_id) -> Optional[dict]:
    """Existing connections as a row of avatars -- the fastest path back
    to a shopfront they already trust."""
    profiles = connected_supplier_profiles(business_id)
    if len(profiles) < MIN_AVATARS:
        return None

    limit = RAIL_LIMITS["your-suppliers"]

    return {
        "id": "your-suppliers",
        "type": "SUPPLIER_AVATARS",
        "title": "Your suppliers",
        "suppliers": feed_suppliers(profiles[:limit]),
        # PAST THE CAP THIS GOES TO MY CONNECTIONS rather than to a
        # screen of its own: the full list of who you trade with is
        # already a screen, already maintained, and already the place a
        # shopkeeper looks for it.
        **_rail_tail("your-suppliers", min(limit, len(profiles)), len(profiles)),
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
    from src.domains.network.community.services import feed_detail_service

    connected = connected_supplier_ids(business_id)
    untried = feed_detail_service.not_ordered_yet_suppliers(business_id)
    if len(untried) < MIN_ITEMS_PER_RAIL:
        return None

    limit = RAIL_LIMITS["not-ordered-yet"]

    return {
        "id": "not-ordered-yet",
        "type": "SUPPLIER_RAIL",
        "title": "Suppliers you haven't ordered from",
        "subtitle": "In reach, and new to you",
        "suppliers": feed_suppliers(untried[:limit], connected_ids=connected),
        **_rail_tail("not-ordered-yet", min(limit, len(untried)), len(untried)),
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

    AND NO RAIL WITHOUT SOMEBODY ACTUALLY NEAR. Sorting by distance is
    not the same as filtering by it -- the nearest of a distant set is
    still distant, and this rail promises "near you" in its own title.
    Beyond MAX_COLLECTION_KM a supplier is dropped rather than shown as
    the best of a bad lot, which means the rail can and should vanish
    for a shop with nobody close. That is the honest answer.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.network.community.services import feed_detail_service

    profile = BusinessProfileRepository.get_for_business(business_id)
    if profile is None:
        return None

    connected = connected_supplier_ids(business_id)

    # DISTANCES AND THE RADIUS CEILING LIVE IN feed_detail_service, so
    # the rail and the screen behind its arrow cannot disagree about
    # what "near" means.
    measured = feed_detail_service.collect_near_you_suppliers(business_id)
    if len(measured) < MIN_ITEMS_PER_RAIL:
        return None
    nearest = measured[: RAIL_LIMITS["collect-near-you"]]

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
        # FIVE ON THE RAIL, because choosing between SUPPLIERS is a
        # slower decision than scanning stock and a long row of them is
        # a chore rather than a choice. The rest are a tap away.
        #
        # AND STRICTLY DISTANCE-ORDERED, at every tier, forever: this is
        # the only rail that prints the number it is sorted by, so any
        # reordering is a contradiction the reader is holding (V2_17 Q5).
        **_rail_tail("collect-near-you", len(nearest), len(measured)),
    }
