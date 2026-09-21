"""
Composing the Community feed.

ORDERING LIVES IN ONE FILE (V2_04 Part 5), and this is it. Scatter the
rules across the section builders and "why is this rail second?"
becomes a question you answer by reading four files and guessing.

THE SERVER DECIDES ORDER, NOT THE APP. The endpoint returns a list of
typed sections and the client renders whatever it is handed, skipping
types it does not recognise. That contract is what makes a seasonal
promo or a paid placement a server change rather than an app release --
and it is stated from the other side in the frontend's own
community/types.ts.

WHY THE SUPPLIER ORDER IS THIS ORDER:

  1  WANTS TO CONNECT      somebody is waiting on a decision. A person
                           blocked on you outranks anything else.
  2  CUSTOMERS GOING QUIET revenue already earned and at risk of
                           leaving. Cheaper to keep than to replace.
  3  YOUR SHOPFRONT        what is stopping you selling. Above growth,
                           because attracting businesses to a shopfront
                           that cannot take their order wastes both.
  4  BUSINESSES NEAR YOU   growth, last. It is the only section that
                           asks the supplier to start something rather
                           than finish it.

DEMAND_GAP_RAIL WOULD BE FIRST, and is absent -- see
supplier_sections' own docstring for why V2_07 defers it.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.domains.network.community.business import sections as business_sections
from src.domains.network.community.supplier import sections as supplier_sections


def feed_for(user_id: str | UUID, role: str) -> List[dict]:
    """The feed for this caller, in the order the server chose.

    ROLE COMES FROM THE TOKEN, never from a query parameter, even
    though V2_04 writes the endpoint as `?role=supplier`. A role a
    caller can ask for is a role a caller can lie about, and the
    business feed is a different privacy surface from the supplier one.
    """
    if role == "supplier":
        return _supplier_feed(user_id)
    if role == "business":
        sections = _business_feed(user_id)
        _count_delivered(user_id, sections)
        return sections
    raise NotFoundError("No community feed for this account type.")


def _count_delivered(business_id, sections: List[dict]) -> None:
    """Record what this render returned, without making anyone wait.

    SERVER-SIDE, AT COMPOSE TIME, AND THAT IS THE DESIGN (V2_19 1.3).
    The composer already knows exactly what it returned -- there is no
    client to trust, no extra round trip, and no double counting when a
    screen re-renders. The device is asked only for taps, because a tap
    is the one thing it alone witnesses.

    THROUGH THE QUEUE, SO A SHOPKEEPER NEVER WAITS ON ANALYTICS. If the
    process dies before the counter lands, a counter was lost. That is
    the right failure: the alternative is a feed that is slower for
    everyone so that a tuning number is never missed.

    AND IT NEVER BREAKS THE FEED. An impression write that raises must
    not turn a working tab into an error -- the measurement exists to
    serve the feed, not the other way round. The queue's own runner
    logs and swallows, and this import is local so a problem in the
    impressions package cannot stop this module being imported at all.

    THE APP CONTEXT IS CAPTURED AND RE-ENTERED, and that is not
    ceremony -- without it this writes NOTHING and says nothing about
    it. The queue is a ThreadPoolExecutor; a worker thread has no Flask
    application context, so db.session raises the moment it is touched,
    and _run_and_track catches the exception so the pool survives. The
    result is a feed that composes perfectly, a queue that drains
    cleanly, and a table that stays empty.

    Found by rendering a real feed against the dev database three times
    and getting zero rows. The unit tests did not catch it because they
    call the repository directly; the test that does is
    test_the_feed_writes_through_the_queue, added with this fix.

    audit_service already solved this the same way, capturing `app`
    from register(); master_scheduler.trigger.py does it too. There is
    no request here to borrow a context from, so the real app object is
    taken out of current_app's proxy before the thread starts.

    BUSINESS ONLY, for now. The supplier feed is a different surface
    with different sections, and nobody has asked a question about it
    that needs measuring yet -- see impression_routes on why that is a
    deliberate future addition rather than an omission.
    """
    from flask import current_app

    from src.domains.network.impressions.services import impression_service
    from src.shared.queue.queue import enqueue

    app = current_app._get_current_object()

    def _write() -> None:
        with app.app_context():
            impression_service.record_delivered(business_id, sections)

    enqueue(_write)


def _business_feed(business_id) -> List[dict]:
    """WHY THE BUSINESS ORDER IS THIS ORDER:

      1  CATEGORIES            the only way to shop when nothing below
                               applies yet, so it never moves and a new
                               user is never handed an empty screen.
      2  TELL US WHAT YOU BUY  only while they have declared nothing.
                               High, because for a shop with no history
                               it is the most useful thing on the
                               screen -- and it vanishes the moment it
                               is answered.
      3  BUY IT AGAIN          their own restocking list. The highest-
                               value rail in the app, and the reason a
                               shopkeeper opens this tab at all.
      4  PICK UP WHERE YOU     products they OPENED and never ordered.
         LEFT OFF              Directly below their own purchase
                               history because it is the same kind of
                               evidence one step weaker: buy-it-again
                               is what they DID, this is what they
                               nearly did. Both are the shop's own
                               actions, and a shop's own actions beat
                               anything the market is doing.

                               IT IS ALSO THE ONLY RAIL THAT READS THE
                               IMPRESSIONS TABLE, which is what stops
                               that table being a measurement nothing
                               consumes.
      5  MOVING FAST           things selling quicker than usual, in
                               the categories this shop buys. Above
                               "stock for your shop" because it is
                               TIME-SENSITIVE: the same product will
                               still be there next week, the reason to
                               look at it today will not. Below "buy it
                               again" because a shop's own restock list
                               beats anything the market is doing.
      6  STOCK FOR YOUR SHOP   what they SAID they buy. Below their
                               own history, which is evidence, and
                               above everything else, because it is the
                               only personal section a shop has before
                               its first order.
      7  YOUR SUPPLIERS        the fastest path back to a shopfront
                               they already trust.
      8  SPONSORED             the one paid slot, below everything the
                               shop earned and above cold discovery.
                               Labelled, and gated on the shop's own
                               categories.
      9  THEY JOINED BECAUSE   suppliers this shop personally invited,
         OF YOU                who signed up and got verified. Above
                               cold discovery because these are people
                               the shopkeeper already trades with
                               offline and vouched for hard enough to
                               go and recruit -- and because inviting
                               somebody was, until now, the one action
                               in this app that got no reply at all.
                               RARE, so it costs the rails below it
                               nothing on the days it is absent.
     10  NOT ORDERED YET       suppliers in reach they have never
                               bought from, connected or not. The ones
                               they already know come first: the trust
                               is done, only the first order is missing.
     11  COLLECT NEAR YOU      growth. The only RAIL asking them to
                               start something rather than continue it
                               -- the same reason businesses_near_you
                               sits last for the supplier.
     12  EXPLORE BY KIND       the door out of the feed entirely, and
                               therefore last. Everything above it is a
                               supplier this shop has some claim on --
                               history, a declaration, an invitation,
                               proximity. This is the way to the ones
                               they have none on, and it is at the
                               bottom because reaching it means
                               somebody went looking. See
                               business_sections.explore_kinds.

    THE PRICE-MOVEMENT RAIL IS STILL ABSENT, deferred by name in V2_09
    Part 5. Sponsored was absent for the same reason until there was
    something to put in it -- an empty paid slot is worse than none --
    and sponsored_supplier still returns None rather than an empty
    shell on a day nobody qualifies.
    """
    sections = [
        business_sections.category_chips(),
        business_sections.tell_us_what_you_buy(business_id),
        business_sections.buy_it_again(business_id),
        # THE ONE SECTION BUILT FROM WHAT THE FEED ITSELF OBSERVED.
        # Everything else here reads orders, declarations or the
        # market; this reads the impressions table, which is what stops
        # that table being a measurement nothing consumes.
        business_sections.picked_up_where_you_left(business_id),
        business_sections.moving_fast(business_id),
        business_sections.stock_for_what_you_buy(business_id),
        business_sections.your_suppliers(business_id),
        # THE ONE PAID SLOT, below everything the shop earned and above
        # cold discovery. It is labelled, it is gated on the shop's own
        # categories, and it is the only section here anybody paid for.
        business_sections.sponsored_supplier(business_id),
        business_sections.invited_suppliers(business_id),
        business_sections.not_ordered_from_yet(business_id),
        business_sections.collect_near_you(business_id),
        # LAST, AND THE ONLY SECTION THAT LEAVES THE FEED. Everything
        # above is a supplier this shop has some claim on; this is the
        # door to the rest. Its own docstring explains why the bottom
        # is the only honest place for it.
        business_sections.explore_kinds(),
    ]
    return [s for s in sections if s is not None]


def _supplier_feed(supplier_user_id) -> List[dict]:
    from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
        SupplierProfileRepository,
    )

    profile = SupplierProfileRepository.get_by_supplier_id(supplier_user_id)
    if profile is None:
        # A supplier whose profile has not been seeded yet -- no
        # sections are computable, and an empty feed is correct.
        return []

    sections = [
        supplier_sections.wants_to_connect(profile),
        supplier_sections.reorder_due(profile),
        supplier_sections.shopfront_health(profile),
        supplier_sections.businesses_near_you(profile),
    ]

    # EVERY BUILDER RETURNS None WHEN IT HAS NOTHING, and they are
    # filtered here rather than each one returning an empty shell. A
    # zero card is worse than no card, and a new supplier should see a
    # nearly empty tab rather than four rows telling them how little
    # they have.
    return [s for s in sections if s is not None]
