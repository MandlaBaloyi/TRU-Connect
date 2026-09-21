"""
The tap endpoint's rate limit -- the one limit in this domain that
cannot wait for the rest.

WHY THIS ONE SHIPS WITH THE FEATURE. Every other route in
network/community is a READ that composes from the caller's own data.
This is the first WRITE the app can drive, in batches, on a timer, from
a device we do not control. Without a limit it is a free write
amplifier against a table that is already the fastest-growing one in
the system by design -- and the grain decision in feed_impression.py
bounds rows by distinct combinations, which bounds nothing at all if a
client is willing to invent combinations.

THE NUMBER IS A PHASE 1 STARTING POINT, same caveat as auth's and
connections' own policies: it is not a production figure, it is a
figure that cannot be embarrassing. A shop scrolling a feed hard
produces well under a hundred taps a minute; a script does not.

BATCHED, SO THE LIMIT IS PER REQUEST AND THE REQUEST CARRIES MANY.
useTapTracking sends one POST with up to MAX_TAPS_PER_REQUEST entries
rather than one POST per tap, which is why a limit this low is
generous rather than restrictive -- and why the per-request cap below
matters as much as the per-minute one.
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

TAP = "20 per minute"

#: HOW MANY TAPS ONE REQUEST MAY CARRY. The limit above bounds
#: requests; without this, one request could carry fifty thousand
#: entries and the rate limit would have bounded nothing that matters.
#: Two ceilings, because the thing being protected is rows, not calls.
MAX_TAPS_PER_REQUEST = 100


def business_key_func() -> str:
    """Keyed by the authenticated shop, not by IP.

    THE SAME REASONING AS connections/rate_limit/policies.py: this
    route already requires a valid JWT, so there is a real identity to
    key by, and two shops behind one township wifi connection must not
    consume each other's allowance.
    """
    return get_jwt_identity() or "anonymous"
