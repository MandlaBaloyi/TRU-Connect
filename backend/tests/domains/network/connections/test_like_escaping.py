"""
LIKE-escaping tests -- a real gap found while reviewing search
behaviour: a literal "%" or "_" typed into a name search used to be
interpreted as a SQL wildcard instead of a literal character.
"""
from __future__ import annotations

from src.domains.network.connections.services import connections_service


def test_literal_percent_does_not_wildcard_match_everything(
    make_business, make_supplier, make_supplier_profile
):
    """Before the fix, searching "%%" (unescaped, this becomes the
    pattern "%%%" -- matches any name at all) would match every
    supplier regardless of name. After the fix, it only matches a
    supplier whose name literally starts with "%%".

    Uses two characters, not one -- a single "%" is correctly
    rejected by the >= 2 character minimum before it ever reaches the
    search/escaping logic this test is actually about."""
    business = make_business()
    supplier_user = make_supplier()
    make_supplier_profile(supplier_user, business_name="Normal Wholesale")

    results = connections_service.search_suppliers("%%", business.id)
    assert results == []


def test_literal_percent_matches_a_name_that_actually_contains_it(
    make_business, make_supplier, make_supplier_profile
):
    business = make_business()
    supplier_user = make_supplier()
    make_supplier_profile(supplier_user, business_name="50% Off Traders")

    results = connections_service.search_suppliers("50%", business.id)
    assert len(results) == 1
    assert results[0]["businessName"] == "50% Off Traders"


def test_literal_underscore_does_not_wildcard_match_any_single_character(
    make_business, make_supplier, make_supplier_profile
):
    """SQL LIKE's "_" matches any single character -- "Xa" would
    wrongly match a search for "X_" before the fix."""
    business = make_business()
    supplier_user = make_supplier()
    make_supplier_profile(supplier_user, business_name="Xa Traders")

    results = connections_service.search_suppliers("X_", business.id)
    assert results == []
