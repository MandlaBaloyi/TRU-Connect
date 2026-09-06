"""
Ownership / IDOR (Insecure Direct Object Reference) tests -- same
convention and purpose as loan_book's own test_ownership.py.

Business A requests a connection to a supplier. Business B -- a
completely separate, real business -- looks at the SAME supplier's
profile using B's own real identity. B must see NOT_REQUESTED, never
A's PENDING -- confirmed against a real database in this session's own
verification run before being written down as a permanent test.
"""
from __future__ import annotations

from src.domains.network.connections.services import (
    discovery_service,
    request_service,
)


def test_connection_status_is_isolated_per_business(make_business, make_supplier, make_supplier_profile):
    business_a = make_business("business-a@example.com")
    business_b = make_business("business-b@example.com")
    supplier_user = make_supplier("supplier@example.com")
    profile = make_supplier_profile(supplier_user, business_name="Shared Supplier")

    request_service.request_connection(business_a.id, profile.id)

    preview_for_a = discovery_service.get_supplier_profile(business_a.id, profile.id)
    preview_for_b = discovery_service.get_supplier_profile(business_b.id, profile.id)

    assert preview_for_a["connectionStatus"] == "PENDING"
    assert preview_for_b["connectionStatus"] == "NOT_REQUESTED"
