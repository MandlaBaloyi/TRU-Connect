"""
The supplier's Community feed, section by section.

THE ORGANISING IDEA (V2_04 §3.2), and it is the whole reason this file
is not a copy of the business side:

  ─────────────────────────────────────────────────────────────────────
  For the business, Community is a MARKET.
  For the supplier, Community is a DEMAND SIGNAL.
  ─────────────────────────────────────────────────────────────────────

A supplier does not shop. Handing them a "For You" rail of other
suppliers is symmetry mistaken for design -- which is exactly what the
tab does today and exactly why it feels like nothing. Their questions
are: who is buying from me and who stopped, who nearby could buy and
does not, and what are they asking for that I do not sell.

FOUR SECTIONS, NOT FIVE. V2_04 §3.3 lists a DEMAND_GAP_RAIL first and
calls it "the single most valuable thing TruConnect can tell a
supplier" -- and V2_07 item C then defers it, because it needs data
volume to be non-embarrassing. It also carries a hard privacy floor
(five distinct businesses before a row may exist), so on an empty
platform it would either render nothing or breach its own rule. It is
absent on purpose, not forgotten.

EVERY SECTION RETURNS NOTHING WHEN IT HAS NOTHING. A zero card is
worse than no card -- the rule the supplier Home already follows, and
the reason a new supplier sees a nearly empty tab rather than four
rows of zeroes telling them how little they have.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.core.base_model import utcnow
from src.domains.network.community.algorithms import distance, reorder_gap


def reorder_due(supplier_profile) -> Optional[dict]:
    """CUSTOMER_RAIL -- connected businesses who have gone quiet.

    THE SECTION THAT TURNS THE TAB INTO A SALES TOOL. The supplier's
    own customers, their own trading history, no privacy question at
    all. A supplier who opens this and reads "usually orders weekly,
    nothing for three weeks" has been handed a phone call worth making.

    ORDERED BY HOW OVERDUE, not by how much they spend. The most
    valuable customer is not the most urgent one -- a big account that
    ordered yesterday needs no call, and a small one three weeks silent
    might already be buying elsewhere.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )
    from src.domains.network.orders.models.stock_order import StockOrder, StockOrderStatus
    from src.extensions import db

    active = ConnectionRequestRepository.list_active_for_supplier_profile(supplier_profile.id)
    if not active:
        return None

    now = utcnow()
    rows = []
    for request in active:
        dates = [
            d[0]
            for d in db.session.query(StockOrder.submitted_at)
            .filter(
                StockOrder.business_id == request.business_id,
                StockOrder.supplier_profile_id == supplier_profile.id,
                StockOrder.submitted_at.isnot(None),
                # A CART IS NOT AN ORDER, and a declined or cancelled one
                # says nothing about a buying rhythm. Counting either
                # would make a supplier who declines a lot look like
                # they have loyal customers.
                StockOrder.status.notin_(
                    [
                        StockOrderStatus.CART,
                        StockOrderStatus.DECLINED,
                        StockOrderStatus.CANCELLED,
                    ]
                ),
                StockOrder.is_deleted.is_(False),
            )
            .all()
        ]
        pattern = reorder_gap.pattern_from(dates, now)
        if not pattern.is_overdue:
            continue

        profile = BusinessProfileRepository.get_for_business(request.business_id)
        rows.append(
            {
                "businessId": str(request.business_id),
                "businessName": (profile.business_name if profile else None) or "A business",
                "photoUrl": _business_photo(profile, request.business_id),
                "orderCount": pattern.order_count,
                "typicalGapDays": pattern.typical_gap_days,
                "daysSinceLastOrder": pattern.days_since_last,
                "daysOverdue": pattern.days_overdue,
            }
        )

    if not rows:
        return None

    rows.sort(key=lambda r: r["daysOverdue"] or 0, reverse=True)
    return {
        "type": "CUSTOMER_RAIL",
        "title": "Customers going quiet",
        "subtitle": "They usually order more often than this",
        "customers": rows,
    }


def wants_to_connect(supplier_profile) -> Optional[dict]:
    """Pending connection requests, surfaced in Community.

    ALREADY BUILT, JUST IN THE WRONG PLACE (V2_04 §3.3, section 3):
    the card lives on Home today. It belongs here because Community is
    where a supplier goes to think about who they trade with, and Home
    is for what needs doing today -- a distinction that only holds if
    each screen stops borrowing the other's content.

    This returns the COUNT and the names, not the request objects. The
    decision screen already exists (supplier/customer-requests) and
    duplicating its payload here would mean two places to keep correct.
    """
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )

    pending = ConnectionRequestRepository.list_pending_for_supplier_profile(supplier_profile.id)
    if not pending:
        return None

    businesses = []
    for request in pending[:10]:
        profile = BusinessProfileRepository.get_for_business(request.business_id)
        businesses.append(
            {
                "businessId": str(request.business_id),
                "businessName": (profile.business_name if profile else None) or "A business",
                "photoUrl": _business_photo(profile, request.business_id),
            }
        )

    return {
        "type": "BUSINESS_AVATARS",
        "title": "Wants to connect",
        "subtitle": f"{len(pending)} waiting for your decision",
        "totalCount": len(pending),
        "businesses": businesses,
    }


def businesses_near_you(supplier_profile, limit: int = 10) -> Optional[dict]:
    """BUSINESS_RAIL -- shops in range with no connection. The growth
    surface.

    THE VISIBILITY RULES ARE NOT RE-IMPLEMENTED HERE. Photos resolve
    through connections._common._resolve_visible_photo_url, the same
    function the profile screens use, with is_active_connection=False
    because by definition nobody in this list is connected. A second
    copy of that rule would drift, and the thing it protects is a
    person's photograph.

    DISTANCE IS COMPUTED, NOT STORED, and businesses without
    coordinates are omitted rather than shown as "unknown distance" --
    a growth rail is a list of people to approach, and one you cannot
    tell the distance to is not actionable.
    """
    from src.domains.business.business_profile.models.business_profile import BusinessProfile
    from src.domains.network.connections.repositories.connection_request_repository import (
        ConnectionRequestRepository,
    )

    lat = supplier_profile.collection_latitude
    lon = supplier_profile.collection_longitude
    if lat is None or lon is None:
        # WITHOUT OUR OWN LOCATION THERE IS NO "NEAR". Returning an
        # unsorted list of every business would be worse than returning
        # nothing -- it would look like a recommendation.
        return None

    connected_ids = {
        str(r.business_id)
        for r in ConnectionRequestRepository.list_active_for_supplier_profile(supplier_profile.id)
    }
    pending_ids = {
        str(r.business_id)
        for r in ConnectionRequestRepository.list_pending_for_supplier_profile(supplier_profile.id)
    }
    seen = connected_ids | pending_ids

    candidates = (
        BusinessProfile.query.filter(
            BusinessProfile.is_deleted.is_(False),
            BusinessProfile.latitude.isnot(None),
            BusinessProfile.longitude.isnot(None),
        )
        .limit(500)
        .all()
    )

    rows = []
    for profile in candidates:
        if str(profile.business_id) in seen:
            continue
        km = distance.km_between(lat, lon, profile.latitude, profile.longitude)
        if km is None:
            continue
        rows.append(
            {
                "businessId": str(profile.business_id),
                "businessName": profile.business_name or "A business",
                "photoUrl": _business_photo(profile, profile.business_id),
                "category": profile.category,
                "distanceKm": km,
            }
        )

    if not rows:
        return None

    rows.sort(key=lambda r: r["distanceKm"])
    return {
        "type": "BUSINESS_RAIL",
        "title": "Businesses near you",
        "subtitle": "Shops in your area you have not connected with",
        "businesses": rows[:limit],
    }


def shopfront_health(supplier_profile) -> Optional[dict]:
    """STOREFRONT_HEALTH -- the specific things stopping them selling.

    NOT VANITY METRICS (V2_04 §3.3, section 5). Every item is something
    a supplier can act on in one tap, and the card disappears entirely
    when there is nothing wrong rather than congratulating them.

    ONE ITEM FROM THE SPEC IS ABSENT AND CANNOT EXIST: V2_04 asks for
    "how many offers have no price". SupplierOffer.price_cents is NOT
    NULL, so an unpriced offer is unrepresentable -- there is no such
    row to count. Reporting a permanent zero would imply we were
    checking something we are not.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer

    live_offers = SupplierOffer.query.filter_by(
        supplier_profile_id=supplier_profile.id, is_archived=False, is_deleted=False
    ).count()

    # UNMATCHED means product_id is null -- the offer exists but is not
    # on the shared catalogue, so it cannot be price-compared or found
    # by a business searching the catalogue rather than this supplier.
    unmatched = SupplierOffer.query.filter_by(
        supplier_profile_id=supplier_profile.id, is_archived=False, is_deleted=False
    ).filter(SupplierOffer.product_id.is_(None)).count()

    issues = []
    if live_offers == 0:
        issues.append(
            {
                "code": "NO_LIVE_OFFERS",
                "message": "You have nothing listed for sale yet.",
                "count": 0,
            }
        )
    if supplier_profile.minimum_order_cents is None:
        issues.append(
            {
                "code": "NO_MINIMUM_ORDER",
                "message": "Set a minimum order so businesses know what to expect.",
                "count": 0,
            }
        )
    if unmatched:
        issues.append(
            {
                "code": "UNMATCHED_OFFERS",
                "message": (
                    f"{unmatched} of your products are not matched to the shared catalogue, "
                    "so businesses searching for them will not find you."
                ),
                "count": unmatched,
            }
        )

    if not issues:
        return None

    return {
        "type": "STOREFRONT_HEALTH",
        "title": "Your shopfront",
        "issues": issues,
    }


def _business_photo(profile, business_id) -> Optional[str]:
    """The visible photo for a business, through the ONE shared rule.

    Deliberately not re-implemented: connections._common owns the
    resolution, both profile screens use it, and the thing it guards is
    somebody's photograph. is_active_connection is passed explicitly by
    each caller because it genuinely differs -- a customer of theirs is
    connected, a business in the growth rail is not.
    """
    if profile is None:
        return None
    from src.domains.auth.repositories.user_repository import UserRepository
    from src.domains.network.connections.services._common import _resolve_visible_photo_url

    user = UserRepository.get_by_id(business_id)
    return _resolve_visible_photo_url(
        profile,
        personal_photo_url=getattr(user, "profile_image_url", None),
        is_active_connection=False,
    )
