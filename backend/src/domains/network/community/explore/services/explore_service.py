"""
Browsing suppliers by what they ARE.

THE FILTER IS A STATED FACT, NEVER A STRING SOMEBODY TYPED. This screen
exists because a business wants to see wholesalers, and the obvious
implementation -- matching the business NAME -- is wrong in both
directions at once. The dev database made it concrete:

    "Qwen Wholesale"          a name filter would match
    "Lepelle Wholesalers"     would match
    "Seshego Cash & Carry"    IS a wholesaler, would NOT match
    "MacMan Businesses"       would not match

and a retailer trading as "Wholesale Beauty Supplies" would be listed
having done nothing wrong. A screen anybody can enter by renaming their
business is a keyword search wearing a filter's clothes. So it reads
supplier_kind, which somebody declared.

THE CURTAIN APPLIES HERE LIKE EVERYWHERE ELSE. This is discovery -- the
most discovery-shaped surface in the app -- so an unverified supplier
does not appear, full stop.

AND THIS IS WHERE TIER ORDERING IS HONEST. Everywhere in For You the
reader came for their own restocking list, so promotion competes with
what they asked for. Here they came to browse suppliers, so showing
them suppliers is the thing they wanted. The organic fact still ranks
first -- see the sort below.
"""
from __future__ import annotations

from typing import List, Optional

from src.domains.network.community.placement import tier_rules

#: The most this screen returns in one page.
PAGE_SIZE = 40


def wholesalers(business_id, *, kind: Optional[str] = None) -> List:
    """Visible suppliers of a given kind, best first.

    THE ORGANIC FACT IS "DO THEY HAVE ANYTHING TO SELL". A supplier
    with an empty catalogue is not a browsing result, they are a
    disappointment with a logo -- and ordering_gate already refuses an
    order from one ("there is nothing to order from an empty
    catalogue"), so listing them here would be offering a door that is
    known to be locked.

    THEN TIER ORDERS THE EQUALS, and this screen is where that is
    defensible: it shows no distance and no score, so its order is not
    a claim the reader can check (V2_17 Q5's test, applied here).

    THEN THE ALPHABET, so the list is deterministic. A screen that
    reorders between identical requests is one nobody can debug, and
    one no supplier can be shown to have been treated fairly by.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierKind,
        SupplierProfile,
    )
    from src.domains.verification.visibility import visible_filter
    from src.extensions import db

    wanted = kind or SupplierKind.WHOLESALER.value

    # ONE QUERY, JOINED TO STOCK. The alternative -- list suppliers,
    # then count each one's products -- is the N+1 this codebase has
    # removed three times.
    profiles = (
        db.session.query(SupplierProfile)
        .join(SupplierOffer, SupplierOffer.supplier_profile_id == SupplierProfile.id)
        .filter(
            visible_filter(),
            SupplierProfile.is_deleted.is_(False),
            SupplierProfile.supplier_kind == wanted,
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
        )
        .distinct()
        .all()
    )

    return sorted(
        profiles,
        key=lambda p: (
            -tier_rules.rank(tier_rules.effective_tier(p)),
            (p.business_name or "").lower(),
        ),
    )


def kinds_with_suppliers() -> List[str]:
    """Which kinds actually have somebody to show.

    THE CHIPS ARE BUILT FROM THIS rather than from the enum, so the
    screen never offers a filter that returns nothing. An empty result
    from a chip the app drew itself reads as broken; a chip that is not
    there reads as "not yet", which is the truth.
    """
    from src.domains.supplier.products.models.supplier_offer import SupplierOffer
    from src.domains.supplier.supplier_profile.models.supplier_profile import (
        SupplierKind,
        SupplierProfile,
    )
    from src.domains.verification.visibility import visible_filter
    from src.extensions import db

    rows = (
        db.session.query(SupplierProfile.supplier_kind)
        .join(SupplierOffer, SupplierOffer.supplier_profile_id == SupplierProfile.id)
        .filter(
            visible_filter(),
            SupplierProfile.is_deleted.is_(False),
            SupplierOffer.is_deleted.is_(False),
            SupplierOffer.is_archived.is_(False),
        )
        .distinct()
        .all()
    )

    found = {getattr(k, "value", k) for (k,) in rows}
    # UNSPECIFIED IS NOT A FILTER. It is the honest default for a
    # supplier who has not said, and "browse the ones who did not tell
    # us what they are" is not a thing anybody wants to tap.
    found.discard(SupplierKind.UNSPECIFIED.value)

    # A STABLE ORDER, from the enum rather than from whatever the
    # database returned, so the chips do not move between visits.
    return [k.value for k in SupplierKind if k.value in found]
