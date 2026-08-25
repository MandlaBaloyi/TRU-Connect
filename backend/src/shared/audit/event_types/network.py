"""
Network's own audit event vocabulary (supplier discovery, connections
between suppliers and businesses) -- moved here from the single flat
AuditEventName enum, same reasoning as event_types/auth.py's own
docstring.
"""
from __future__ import annotations

import enum


class NetworkAuditEvent(str, enum.Enum):
    SUPPLIER_SEARCH_RATE_LIMITED = "network.supplier_search_rate_limited"
    CONNECTION_REQUEST_RATE_LIMITED = "network.connection_request_rate_limited"
    # Reverse direction (supplier searching for businesses, Find
    # Business). Deliberately a distinct event from
    # SUPPLIER_SEARCH_RATE_LIMITED above rather than reusing it -- that
    # name means "the supplier-search action got rate-limited"
    # (business searching FOR suppliers), which is not what's happening
    # here. This event name mirrors it for the other direction.
    BUSINESS_SEARCH_RATE_LIMITED = "network.business_search_rate_limited"
