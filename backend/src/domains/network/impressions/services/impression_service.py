"""
Turning a composed feed into counters.

TWO HALVES, WRITTEN DIFFERENTLY, AND THE ASYMMETRY IS THE DESIGN
(V2_19 1.3):

  DELIVERED IS RECORDED SERVER-SIDE, at compose time. The composer
  already knows exactly what it returned -- there is no client to
  trust, no extra round trip, and no double counting when a screen
  re-renders or the user pulls to refresh a cached response.

  TAPPED COMES FROM THE APP, because only the device knows. It is the
  one number we cannot observe ourselves, which is why it is the one
  number a client is allowed to assert.

EVERYTHING HERE RUNS THROUGH shared/queue. A shopkeeper waiting on
their feed must never wait on an analytics write; if the counter is
lost because the process died, the answer is that a counter was lost,
not that a feed was slow. Callers enqueue, they do not await.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Sequence
from uuid import UUID as UUIDType

from src.domains.network.impressions.models.feed_impression import (
    ImpressionItemType,
)
from src.domains.network.impressions.repositories.impression_repository import (
    ImpressionRepository,
    ImpressionRow,
)

#: How the three card-bearing section shapes name their list, and what
#: kind of thing is in it.
#:
#: DRIVEN BY THE PAYLOAD, NOT BY THE SECTION TYPE, because the mapping
#: from type to contents is not one-to-one: SUPPLIER_RAIL and
#: SUPPLIER_AVATARS both carry "suppliers", and a future mixed rail
#: would carry both keys. Reading the keys that are actually present
#: means a new section type measures itself the day it ships, with no
#: edit here at all.
_CARD_KEYS = (
    ("products", ImpressionItemType.PRODUCT),
    ("suppliers", ImpressionItemType.SUPPLIER),
    ("categories", ImpressionItemType.CATEGORY),
)


def rows_for_sections(sections: Sequence[dict]) -> List[ImpressionRow]:
    """Every countable card in a composed feed, in order.

    SECTIONS THAT CARRY NO CARDS ARE NOT COUNTED, and that is a
    decision rather than an oversight. PROMO carries a banner and
    EXPLORE_KINDS carries four doorways -- neither is an item a shop
    can want, and every falsifier this table exists to answer
    (interleave's rail ceiling, tier_rules' distance band, velocity's
    window) is phrased about rails of products and suppliers. Adding
    them later is one entry in _CARD_KEYS plus one enum member; adding
    them now would be measuring something before anyone has a question
    about it.

    SPONSORED_SUPPLIER IS COUNTED, and it is the one that pays. It
    carries a single "supplier" rather than a list, so it is handled
    explicitly below rather than being quietly missed by a loop that
    only understands plurals -- which is exactly the bug that would
    make the one billable section the one section with no data.
    """
    rows: List[ImpressionRow] = []

    for section in sections:
        rail = section.get("id")
        if not rail:
            continue

        for key, item_type in _CARD_KEYS:
            cards = section.get(key)
            if not isinstance(cards, list):
                continue
            for position, card in enumerate(cards):
                row = _row(rail, position, card, item_type)
                if row is not None:
                    rows.append(row)

        sponsored = section.get("supplier")
        if isinstance(sponsored, dict):
            row = _row(rail, 0, sponsored, ImpressionItemType.SUPPLIER)
            if row is not None:
                rows.append(row)

    return rows


def _row(
    rail: str, position: int, card: dict, item_type: ImpressionItemType
) -> Optional[ImpressionRow]:
    """One card, or None when it carries nothing to count by.

    A CATEGORY CHIP IS IDENTIFIED BY ITS VALUE, not by an id, because it
    has none -- it is a taxonomy entry, and "bakery" is as stable an
    identifier as any row id would be.
    """
    if not isinstance(card, dict):
        return None

    item_id = card.get("id") or card.get("value")
    if not item_id:
        return None

    # WHO WOULD BE BILLED. A supplier card IS the supplier; a product
    # card names the supplier who offered it. A category chip names
    # nobody, which is why this is nullable on the model.
    supplier_id = card.get("supplierId") if item_type is ImpressionItemType.PRODUCT else None
    if item_type is ImpressionItemType.SUPPLIER:
        supplier_id = card.get("id")

    return ImpressionRow(
        rail=rail,
        position=position,
        item_id=str(item_id)[:64],
        item_type=item_type,
        supplier_profile_id=supplier_id,
    )


def record_delivered(
    business_id: UUIDType, sections: Sequence[dict], *, on: Optional[date] = None
) -> int:
    """Count everything this feed returned. Call from inside the queue.

    RETURNS THE ROW COUNT so a test can assert the walk found what it
    should. Nothing in the request path reads it.
    """
    rows = rows_for_sections(sections)
    return ImpressionRepository.bump(business_id, rows, column="delivered", on=on)


def record_taps(
    business_id: UUIDType,
    taps: Sequence[ImpressionRow],
    *,
    on: Optional[date] = None,
) -> int:
    """Count a batch of taps the device reported.

    A BATCH, NOT ONE CALL PER TAP, matching the delivered side. The
    route receives up to MAX_TAPS_PER_REQUEST entries in one request;
    turning those into one queue job per tap would mean a hundred
    background jobs and a hundred round trips to write a hundred
    counters that one statement handles.

    THE DEVICE NAMES THE GRAIN, WHICH MEANS THE DEVICE CAN LIE, and it
    is worth being clear about what that does and does not buy an
    attacker. The worst case is a shop inflating the tap count on cards
    it was shown -- which corrupts OUR tuning data about OUR feed, and
    nothing else. It cannot be spent, it does not change what anybody
    is charged today, and the business_id comes from the token rather
    than the payload, so one shop cannot write another's numbers.

    WHEN THE SPONSORED SLOT IS ACTUALLY BILLED that calculus changes,
    because a tap will be worth money. The answer then is to bill on
    `delivered` -- which is server-observed and unforgeable -- and to
    treat `tapped` as reporting rather than as an invoice line. Written
    down here because the temptation to bill per tap will arrive long
    after everyone has forgotten that this number is client-asserted.
    """
    return ImpressionRepository.bump(business_id, taps, column="tapped", on=on)
