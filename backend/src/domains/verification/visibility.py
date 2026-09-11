"""
THE CURTAIN. Whether a supplier is visible to buyers at all.

  ─────────────────────────────────────────────────────────────────────
  A supplier builds EVERYTHING and sells NOTHING until verified.
  ─────────────────────────────────────────────────────────────────────

WHAT THIS IS FOR (V2_03 Part 4.5, V2_12 Phase 1). A supplier signs up,
completes a profile, imports a three-thousand-line catalogue, sets
their terms and invites connections -- and no business can find them.
The day verification passes, the whole shopfront turns on at once.

WHY A CURTAIN AND NOT A WALL. A hard gate would make a supplier wait,
idle, for a decision before they could do any of the slow work. That is
both worse for them and worse for us: they arrive on day one of being
allowed to trade facing an empty catalogue. The curtain lets the slow
work happen during the wait, and it is honest in a way a wall is not --
we never took an hour of somebody's time on the promise of business we
had not yet decided to deliver.

WE HIDE THE SUPPLIER, NOT MERELY THEIR OFFERS. This was a real fork,
decided deliberately. Hiding only the offers leaves the shop findable
and empty, and a business who opens an empty shop concludes the
platform is broken rather than that the supplier is pending. It would
also leak the existence of accounts that have not passed checks. So an
unverified supplier does not appear in search, cannot be connected to,
and has no storefront: they do not exist to buyers yet.

THE ONE PLACE THIS IS DEFINED. Every business-facing read filters
through this module -- never by writing `verification_status ==` by
hand somewhere else. A visibility rule applied per-endpoint is a rule
that leaks the first time somebody adds an endpoint, which is why
tests/architecture/test_verification_visibility.py fails the build if a
query reaches SupplierProfile without going through here.

NOT A SUPPLIER-SIDE RULE. A supplier always sees their own catalogue,
inventory, orders and settings in full, verified or not. Nothing in
this module belongs anywhere near supplier-facing code -- applying it
there would hide a supplier's own shop from themselves, which is the
opposite of the design.
"""
from __future__ import annotations

from src.domains.supplier.supplier_profile.models.supplier_profile import (
    SupplierProfile,
    SupplierVerificationStatus,
)

#: The statuses that let a supplier be seen by buyers.
#:
#: A TUPLE, AND DELIBERATELY NOT `!= UNVERIFIED`. Stating what is
#: allowed rather than what is forbidden means a status added later
#: (APPEALING, SUSPENDED, EXPIRED) defaults to INVISIBLE. A negative
#: test would silently make every new state sellable, and the failure
#: would be silent in exactly the direction that costs money.
VISIBLE_STATUSES = (SupplierVerificationStatus.VERIFIED,)


def is_visible_to_buyers(profile) -> bool:
    """Can a business see this supplier at all?

    Accepts a SupplierProfile or None -- None is not visible, so
    callers that may hold a missing profile do not each need their own
    guard. A supplier with no profile row has certainly not been
    verified.
    """
    if profile is None:
        return False
    return profile.verification_status in VISIBLE_STATUSES


def visible_filter():
    """The SQLAlchemy predicate, for queries that must not load rows
    they are only going to discard.

    Use this in the repository:

        SupplierProfile.query.filter(visible_filter(), ...)

    rather than filtering in Python after the fact. A LIMIT applied
    before an in-Python filter returns fewer rows than asked for --
    a search for 20 suppliers would quietly return 3 because 17
    unverified ones used up the limit.
    """
    return SupplierProfile.verification_status.in_(VISIBLE_STATUSES)


def visible_supplier_ids_filter(column):
    """The same rule expressed against a FOREIGN KEY, for tables that
    reference a supplier rather than being one -- offers, storefronts,
    pinned products.

        SupplierOffer.query.filter(
            visible_supplier_ids_filter(SupplierOffer.supplier_id)
        )

    A subquery rather than a join, so callers keep whatever joins they
    already have and the rule cannot change the shape of their result
    set (a join to a one-to-one table is harmless until the day it
    isn't, and then it duplicates rows).
    """
    from src.extensions import db

    return column.in_(
        db.session.query(SupplierProfile.supplier_id).filter(
            visible_filter(),
            SupplierProfile.is_deleted.is_(False),
        )
    )
