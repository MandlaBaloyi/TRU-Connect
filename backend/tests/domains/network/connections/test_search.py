"""
Supplier Discovery search tests -- name/business-name search ONLY now.

Phone/email exact-match search was intentionally REMOVED (see
connections_service.py's own _dispatch_search docstring): even masked
in the response, it let someone probe arbitrary phone numbers/emails
one at a time to learn who's registered, independent of any real
relationship with them -- a genuine enumeration vector, not a
theoretical one. The tests that used to prove phone/email matching
worked are gone from this file; in their place,
test_searching_by_a_real_registered_phone_or_email_no_longer_matches
below proves the vector is actually closed, not just that the old code
path was deleted.

Every test here still runs against a real PostgreSQL 16 instance (see
conftest.py), matching the original file's own discipline.

search_suppliers takes a viewer_id (business_id) -- added for
per-result photo resolution (see connections_service.py's own
_dispatch_search docstring); every call below passes viewer_business.id.
"""
from __future__ import annotations

import pytest

from src.domains.network.connections.services import connections_service
from src.domains.network.connections.services.errors import InvalidSearchQueryError
from src.shared.validation.identifiers import normalize_email, normalize_phone


@pytest.fixture()
def abc_wholesale(make_supplier, make_supplier_profile):
    """Still seeded with a real normalized_phone/normalized_email --
    those columns are unrelated to search now (see
    SupplierProfileRepository's own module docstring: still used for
    the masked-contact-detail display on an existing connection
    request, a different concern from search). Having a real value
    here is exactly what lets
    test_searching_by_a_real_registered_phone_or_email_no_longer_matches
    prove something real, rather than just asserting against an empty
    field."""
    supplier_user = make_supplier("abcwholesale@example.com")
    return make_supplier_profile(
        supplier_user,
        business_name="ABC Wholesale",
        category="Wholesale beverages",
        location="Polokwane",
        normalized_phone=normalize_phone("071 234 5678"),
        normalized_email=normalize_email("Orders@ABCWholesale.co.za"),
    )


@pytest.fixture()
def viewer_business(make_business):
    return make_business("search-viewer@example.com")


def test_search_by_name_prefix(abc_wholesale, viewer_business):
    results = connections_service.search_suppliers("ABC", viewer_business.id)
    assert len(results) == 1
    assert results[0]["businessName"] == "ABC Wholesale"


def test_search_by_name_prefix_is_case_insensitive(abc_wholesale, viewer_business):
    results = connections_service.search_suppliers("abc", viewer_business.id)
    assert len(results) == 1
    assert results[0]["businessName"] == "ABC Wholesale"


def test_name_search_is_prefix_only_not_substring(abc_wholesale, viewer_business):
    """file.txt §4: "should NOT expose everybody" -- a substring that
    only appears mid-name must NOT match. Confirmed against a real DB:
    a `contains` match here would also silently defeat
    ix_supplier_profiles_business_name's own usability at scale."""
    results = connections_service.search_suppliers("Wholesale", viewer_business.id)
    assert results == []


def test_search_result_shape_has_no_matched_field_or_identifier(abc_wholesale, viewer_business):
    """Regression test for the shape simplification itself:
    matchedField/maskedMatchedIdentifier must be genuinely GONE, not
    just always "NAME"/"" -- see SupplierProfile.to_search_result_dict's
    own docstring for why they were removed rather than left constant."""
    results = connections_service.search_suppliers("ABC", viewer_business.id)
    assert "matchedField" not in results[0]
    assert "maskedMatchedIdentifier" not in results[0]
    assert set(results[0].keys()) == {
        "id",
        "businessName",
        "category",
        "location",
        "verificationStatus",
        "photoUrl",
    }


def test_searching_by_a_real_registered_phone_or_email_no_longer_matches(abc_wholesale, viewer_business):
    """THE core regression test for this whole redesign: abc_wholesale
    has a real, stored normalized_phone/normalized_email (see the
    fixture above) -- searching by either must now return NOTHING,
    proving the enumeration vector is actually closed, not just that
    the old phone/email code branches were deleted. Before this
    redesign, both of these queries would have returned exactly this
    supplier."""
    assert connections_service.search_suppliers("071 234 5678", viewer_business.id) == []
    assert connections_service.search_suppliers("orders@abcwholesale.co.za", viewer_business.id) == []


def test_query_below_minimum_length_raises(viewer_business):
    with pytest.raises(InvalidSearchQueryError):
        connections_service.search_suppliers("A", viewer_business.id)


def test_no_match_returns_empty_not_an_error(abc_wholesale, viewer_business):
    results = connections_service.search_suppliers("Zzz Nonexistent", viewer_business.id)
    assert results == []
