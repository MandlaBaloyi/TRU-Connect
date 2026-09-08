"""
Tests for the "Disconnect from this Supplier" and "Report" services --
built after a real, tested migration bug fix (b8e4f1a9c3d7's own
history: uppercase enum labels, not the lowercase .value strings,
confirmed against the real database before trusting either feature).
"""
from __future__ import annotations

import pytest

from src.domains.network.connections.models.connection_request import ConnectionRequest, ConnectionRequestStatus
from src.domains.network.connections.models.supplier_report import SupplierReport
from src.domains.network.connections.services import (
    connection_list_service,
    report_service,
    request_service,
)
from src.domains.network.connections.services.errors import (
    ConnectionNotActiveError,
    ConnectionRequestNotFoundError,
    SupplierNotFoundError,
)
from src.domains.supplier.products.models.supplier_offer import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.extensions import db


def _make_product(profile_id, name, category, price_cents, selling_unit):
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    return SupplierOfferRepository.create(
        profile_id, name, category, price_cents, selling_unit,
        sku=generate_sku(profile_id), product_code=generate_product_code(),
    )


def _make_active_connection(business, supplier_profile):
    request_service.request_connection(business.id, supplier_profile.id)
    request = ConnectionRequest.query.filter_by(
        business_id=business.id, supplier_profile_id=supplier_profile.id
    ).first()
    request.status = ConnectionRequestStatus.ACTIVE
    db.session.commit()


# --- end_connection -----------------------------------------------------


def test_end_connection_transitions_the_same_row_to_ended(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Ending Co")
    _make_active_connection(business, profile)

    result = connection_list_service.end_connection(business.id, profile.id, "NO_LONGER_NEEDED", "Switched suppliers")

    assert result["connectionStatus"] == "ENDED"
    row = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert row.status == ConnectionRequestStatus.ENDED
    assert row.ended_details == "Switched suppliers"


def test_end_connection_disappears_from_active_connections(make_business, make_supplier, make_supplier_profile):
    """THE REAL BEHAVIOUR THIS FEATURE IS FOR -- vanishes from My
    Connections' own active list the moment it's ended."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Vanishing Co")
    _make_active_connection(business, profile)

    connection_list_service.end_connection(business.id, profile.id, "BAD_EXPERIENCE", None)

    active = connection_list_service.get_my_connections(business.id, "business")
    assert active == []


def test_end_connection_raises_for_no_connection_at_all(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Never Connected Co")

    with pytest.raises(ConnectionRequestNotFoundError):
        connection_list_service.end_connection(business.id, profile.id, "OTHER", None)


def test_end_connection_raises_for_a_pending_connection(make_business, make_supplier, make_supplier_profile):
    """A PENDING request isn't an active relationship to end -- same
    distinction can_place_order already enforces elsewhere in this
    domain."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Still Pending Co")
    request_service.request_connection(business.id, profile.id)  # stays PENDING

    with pytest.raises(ConnectionNotActiveError):
        connection_list_service.end_connection(business.id, profile.id, "OTHER", None)


def test_end_connection_raises_for_an_already_ended_connection(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Twice Ended Co")
    _make_active_connection(business, profile)
    connection_list_service.end_connection(business.id, profile.id, "OTHER", None)

    with pytest.raises(ConnectionNotActiveError):
        connection_list_service.end_connection(business.id, profile.id, "OTHER", None)


# --- list_ended_connections ----------------------------------------------


def test_list_ended_connections_returns_real_ended_ones(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Listed Ended Co")
    _make_active_connection(business, profile)
    connection_list_service.end_connection(business.id, profile.id, "FOUND_BETTER_SUPPLIER", "Found a cheaper one")

    results = connection_list_service.list_ended_connections(business.id)

    assert len(results) == 1
    assert results[0]["name"] == "Listed Ended Co"
    assert results[0]["endedReason"] == "FOUND_BETTER_SUPPLIER"
    assert results[0]["endedDetails"] == "Found a cheaper one"
    assert results[0]["otherPartyId"] == str(profile.id)


def test_list_ended_connections_excludes_still_active_ones(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Still Active Co")
    _make_active_connection(business, profile)

    results = connection_list_service.list_ended_connections(business.id)

    assert results == []


# --- request_connection / request_connection_to_business: reconnecting
# after ENDED -- a REAL BUG, found and fixed after direct report.
# _handle_existing_connection only ever special-cased DECLINED; every
# other non-PENDING/ACTIVE status (including ENDED) fell through to a
# silent no-op that returned the stale status without ever creating a
# new pending state. A business disconnecting and then either side
# trying to reconnect got a 200 response with nothing actually
# happening -- invisible to every list on both sides. -----------------


def test_reconnecting_after_ended_resets_to_pending(make_business, make_supplier, make_supplier_profile):
    """THE EXACT REPORTED SYMPTOM, reproduced and proven fixed."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Reconnect Co")
    _make_active_connection(business, profile)
    connection_list_service.end_connection(business.id, profile.id, "NO_LONGER_NEEDED", None)

    result = request_service.request_connection(business.id, profile.id)

    assert result["connectionStatus"] == "PENDING"
    row = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert row.status == ConnectionRequestStatus.PENDING


def test_reconnecting_after_ended_clears_the_old_end_reason(make_business, make_supplier, make_supplier_profile):
    """ended_reason/ended_details are no longer relevant once a new
    connection attempt is underway."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Cleared Reason Co")
    _make_active_connection(business, profile)
    connection_list_service.end_connection(business.id, profile.id, "BAD_EXPERIENCE", "It was bad")

    request_service.request_connection(business.id, profile.id)

    row = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert row.ended_reason is None
    assert row.ended_details is None


def test_reconnecting_after_ended_is_not_rate_limited(make_business, make_supplier, make_supplier_profile):
    """Deliberately different from DECLINED's own retry path -- ending
    a connection is voluntary, not an adversarial rejection, so
    repeatedly disconnecting and reconnecting is never blocked."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="No Rate Limit Co")

    for _ in range(10):
        _make_active_connection(business, profile)
        connection_list_service.end_connection(business.id, profile.id, "OTHER", None)
        result = request_service.request_connection(business.id, profile.id)
        assert result["connectionStatus"] == "PENDING"
        row = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
        row.status = ConnectionRequestStatus.ACTIVE
        db.session.commit()


def test_reconnecting_after_ended_also_works_from_the_supplier_initiated_direction(
    make_business, make_supplier, make_supplier_profile, make_business_profile
):
    """request_connection_to_business shares the same
    _handle_existing_connection -- this fix must apply to a
    supplier-initiated reconnect too, not just the business-initiated
    path exercised above."""
    business = make_business()
    business_profile = make_business_profile(business, business_name="Supplier Side Reconnect Target")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Supplier Side Reconnect Co")
    _make_active_connection(business, profile)
    connection_list_service.end_connection(business.id, profile.id, "OTHER", None)

    result = request_service.request_connection_to_business(supplier_user.id, business_profile.id)

    assert result["connectionStatus"] == "PENDING"


# --- report_supplier ------------------------------------------------------


def test_report_supplier_creates_a_real_persisted_record(make_business, make_supplier, make_supplier_profile):
    """THE REAL GUARANTEE -- a genuine, permanent database row, not
    just an email fire-and-forget. See SupplierReport's own model
    docstring."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Reported Co")

    result = report_service.report_supplier(
        business.id, profile.id, "SUSPECTED_SCAM", "Asked for payment upfront then vanished"
    )

    assert result["status"] == "SUBMITTED"
    report = SupplierReport.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert report is not None
    assert report.reason.value == "suspected_scam"
    assert report.details == "Asked for payment upfront then vanished"


def test_report_supplier_never_requires_a_connection(make_business, make_supplier, make_supplier_profile):
    """Deliberately different from ordering/contact details -- a
    genuine scam concern should be reportable regardless of connection
    status."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Never Connected Reported Co")
    # No connection made at all.

    result = report_service.report_supplier(business.id, profile.id, "OTHER", "Suspicious listing")

    assert result["status"] == "SUBMITTED"


def test_report_supplier_raises_for_a_genuinely_nonexistent_supplier(make_business):
    business = make_business()
    import uuid

    with pytest.raises(SupplierNotFoundError):
        report_service.report_supplier(business.id, uuid.uuid4(), "OTHER", None)


# --- report_supplier: product-level reports ------------------------------


def test_report_supplier_with_a_real_product_id_records_it(make_business, make_supplier, make_supplier_profile):
    """THE REAL NEW BEHAVIOUR -- "Report this product" from the
    product screen's own 3-dot menu attaches a real product to the
    same underlying report."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Product Reported Co")
    product = _make_product(profile.id, "Suspicious Item", ProductCategory.OTHER, 1000, ProductUnit.EACH)

    report_service.report_supplier(business.id, profile.id, "FAKE_PRODUCTS", "Looks counterfeit", product_id=product.id)

    report = SupplierReport.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert report.product_id == product.id


def test_report_supplier_without_a_product_id_leaves_it_null(make_business, make_supplier, make_supplier_profile):
    """The catalogue's own "Report" (not product-specific) still works
    exactly as before -- product_id stays null."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Supplier Reported Co")

    report_service.report_supplier(business.id, profile.id, "SUSPECTED_SCAM", None)

    report = SupplierReport.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert report.product_id is None


def test_report_supplier_silently_drops_a_product_id_belonging_to_a_different_supplier(
    make_business, make_supplier, make_supplier_profile
):
    """THE REAL IDOR CHECK -- a real product id, just under a different
    supplier than the one actually being reported, must never be
    trusted. Silently dropped (product_id ends up null), not an
    error -- a mismatched id shouldn't block a genuine report, it
    should just not misleadingly attach the wrong product to it."""
    business = make_business()
    owner = make_supplier("report-product-owner@example.com")
    owner_profile = make_supplier_profile(owner, business_name="Real Owner Co")
    reported = make_supplier("report-product-reported@example.com")
    reported_profile = make_supplier_profile(reported, business_name="Actually Reported Co")
    other_suppliers_product = _make_product(owner_profile.id, "Not Theirs", ProductCategory.OTHER, 1000, ProductUnit.EACH)

    report_service.report_supplier(
        business.id, reported_profile.id, "OTHER", None, product_id=other_suppliers_product.id
    )

    report = SupplierReport.query.filter_by(business_id=business.id, supplier_profile_id=reported_profile.id).first()
    assert report is not None
    assert report.product_id is None


def test_report_supplier_silently_drops_a_genuinely_nonexistent_product_id(
    make_business, make_supplier, make_supplier_profile
):
    import uuid

    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Fake Product Id Co")

    result = report_service.report_supplier(business.id, profile.id, "OTHER", None, product_id=uuid.uuid4())

    assert result["status"] == "SUBMITTED"
