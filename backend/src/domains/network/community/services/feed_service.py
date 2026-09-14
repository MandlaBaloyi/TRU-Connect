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
        return _business_feed(user_id)
    raise NotFoundError("No community feed for this account type.")


def _business_feed(business_id) -> List[dict]:
    """WHY THE BUSINESS ORDER IS THIS ORDER:

      1  CATEGORIES            the only way to shop when nothing below
                               applies yet, so it never moves and a new
                               user is never handed an empty screen.
      2  BUY IT AGAIN          their own restocking list. The highest-
                               value rail in the app, and the reason a
                               shopkeeper opens this tab at all.
      3  YOUR SUPPLIERS        the fastest path back to a shopfront
                               they already trust.
      4  NOT ORDERED YET       a connection that stalled after the
                               handshake -- the cheapest order to win,
                               because the trust already happened.
      5  COLLECT NEAR YOU      growth, last. The only section asking
                               them to start something rather than
                               continue it -- the same reason
                               businesses_near_you sits last for the
                               supplier.

    SPONSORED AND THE PRICE-MOVEMENT RAIL ARE ABSENT. The price rail is
    deferred by name in V2_09 Part 5; sponsored has nothing to put in it
    until something is sold, and an empty paid slot is worse than none.
    """
    sections = [
        business_sections.category_chips(),
        business_sections.buy_it_again(business_id),
        business_sections.your_suppliers(business_id),
        business_sections.connected_but_never_ordered(business_id),
        business_sections.collect_near_you(business_id),
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
