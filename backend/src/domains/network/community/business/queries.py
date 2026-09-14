"""
Reading the data the business feed is built from.

SPLIT OUT OF sections.py, which had grown to hold two different kinds
of thing: seven section builders and eleven private helpers. Opening it
to review one builder meant scrolling past card shaping and SQL that
had nothing to do with it.

EVERY QUERY HERE APPLIES THE CURTAIN. An unverified supplier is not
findable, and a discovery surface is exactly where a bypass hides --
nobody notices an EXTRA card. tests/architecture/test_verification_curtain.py
fails the build if anything here reaches a supplier through the ungated
lookup.
THE NAMES LOST THEIR LEADING UNDERSCORE in the split. A
leading underscore means "private to this module", and these are now
imported across modules -- keeping it would have been a comment that
contradicted the import above it.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

def connected_supplier_ids(business_id) -> set:
    """Just the ids, for badging and ordering -- no profile loads.

    Separate from connected_supplier_profiles because most callers only
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


def visible_suppliers_with_stock(limit: int = 200) -> List:
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


def connected_supplier_profiles(business_id) -> List:
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


def visible_offers(product_ids: List[UUID]) -> List:
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


def last_active_map(profiles: List) -> dict:
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
