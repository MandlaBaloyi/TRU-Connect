"""
geocoding's own rate-limit policy -- lives HERE, not in
security/rate_limit/, same domain-owns-its-own-policy split as
orders/rate_limit/policies.py's own docstring explains in full.

Guards against one authenticated user's own app accidentally hammering
this endpoint (e.g. a bug that fires a reverse-geocode call on every
pixel of map movement instead of a debounced settle) rather than
malicious abuse -- the free Mapbox tier is generous (100k/month) and
this route requires a valid JWT already, so the real risk here is a
frontend bug burning through it, not an attacker. Deliberately no
RATE_LIMIT_AUDIT_EVENTS mapping (unlike orders'/connections' own
policies.py) -- nothing behind this route moves money or exposes
another user's data, so a rate-limit hit here isn't a security event
worth auditing; revisit if that ever changes.

60/minute, not the original 30 -- raised after live testing showed
the OLD default map center (geometric middle of South Africa, nowhere
near any real business) forced long-distance panning that fired many
requests in a burst and tripped the limit for real. The frontend now
opens the picker on the device's actual current location instead
(MapPickerModal.tsx), which should make hitting even 30/minute rare
in normal use -- this extra headroom is deliberate safety margin for
the times a fix isn't available and someone still has to pan a
distance, not a sign the debounce itself needs retuning.
"""
from __future__ import annotations

from flask_jwt_extended import get_jwt_identity

REVERSE_GEOCODE = "60 per minute"
# Typing naturally fires far more /suggest calls than panning fires
# reverse-geocode calls (one per keystroke pause, not one per map
# settle) -- a separate, more generous limit for exactly that, not a
# sign search is treated as lower-risk than the map picker.
SEARCH_SUGGEST = "90 per minute"
SEARCH_RETRIEVE = "30 per minute"


def user_key_func() -> str:
    """Keyed by the authenticated user's own identity, not IP -- this
    route requires a valid JWT already (any role, see
    geocoding_routes.py's own docstring on why no role_required)."""
    return get_jwt_identity() or "anonymous"
