"""
How far apart two points are, in kilometres.

WRITTEN RATHER THAN IMPORTED because nothing in this codebase computed
a distance before -- the geocoding domain resolves addresses to
coordinates and stops there. Both sides already carry coordinates
(BusinessProfile.latitude/longitude and SupplierProfile.collection_*),
so this is the one missing piece rather than a new data model.

HAVERSINE, NOT A PROJECTION OR POSTGIS. At South African
neighbourhood distances -- the only range that matters for "shops near
you" -- haversine is accurate to metres, and metres are far below the
precision anybody acts on. PostGIS would be the right answer for
polygon delivery areas or for sorting a hundred thousand rows in the
database; it is a deployment dependency we do not need to take on to
answer "is this shop within 15km".

COMPUTED IN PYTHON, ON A SMALL SET, and that is a deliberate limit. A
supplier's candidate businesses are already narrowed by connection
status before this runs. If that set ever grows past a few thousand,
this becomes a database-side calculation -- and the fact that it is
one small function is what makes that swap cheap.
"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Optional

#: Mean radius. The equatorial and polar radii differ by ~21km, which
#: at neighbourhood scale moves an answer by centimetres.
EARTH_RADIUS_KM = 6371.0088


def km_between(
    lat_a: Optional[float],
    lon_a: Optional[float],
    lat_b: Optional[float],
    lon_b: Optional[float],
) -> Optional[float]:
    """Great-circle distance, or None if either point is unknown.

    NONE RATHER THAN A SENTINEL like -1 or a very large number. A
    business that has not set a location is not "infinitely far away";
    the distance is unknown, and a caller sorting by distance has to
    decide what to do about that rather than being handed a number
    that sorts plausibly and means nothing.
    """
    if lat_a is None or lon_a is None or lat_b is None or lon_b is None:
        return None

    # Numeric(9,6) columns arrive as Decimal, and math functions want
    # floats -- converting here means no caller has to remember.
    lat_a, lon_a, lat_b, lon_b = (float(lat_a), float(lon_a), float(lat_b), float(lon_b))

    d_lat = radians(lat_b - lat_a)
    d_lon = radians(lon_b - lon_a)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(d_lon / 2) ** 2
    )
    return round(2 * EARTH_RADIUS_KM * asin(sqrt(a)), 1)
