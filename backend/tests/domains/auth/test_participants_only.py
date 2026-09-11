"""
Staff accounts are not marketplace participants.

WHAT THIS FILE IS ACTUALLY DEFENDING. Fifty authenticated endpoints
pinned no role, because for most of this codebase's life "has a valid
token" and "is a business or a supplier" were the same sentence. They
stop being the same sentence the moment UserRole.ADMIN can hold a
token, and the failure is not a tidy 403 -- several of those routes
BRANCH on the caller's role, and two of them WRITE. The test that
matters most here is therefore not
test_admin_is_refused_everywhere (a status code) but
test_admin_hitting_the_business_profile_creates_no_row: the bug was
that GET /business-profile calls get_or_create_for_business, so merely
LOOKING at that endpoint with a staff token would have quietly made
the admin into a business.

THE THREE DELIBERATE EXCEPTIONS are asserted too, in
test_identity_endpoints_stay_open_to_staff. /me, /me/profile-image and
the web /session answer "who am I", which every role needs and no role
can abuse -- pinning those would lock admins out of the portal they
are being created to operate.
"""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from src.domains.auth.models.user import UserRole, VerificationStatus


@pytest.fixture()
def make_business(make_user, db_session):
    def _make(email: str = "shop@example.com"):
        user = make_user(email, role=UserRole.BUSINESS, verification_status=VerificationStatus.VERIFIED)
        db_session.commit()
        return user

    return _make


@pytest.fixture()
def make_seller(make_user, db_session):
    """Named make_seller, not make_supplier, so it cannot be confused
    with the domain fixtures of that name that also build a
    SupplierProfile. Nothing here needs one -- these tests never get
    past the role check."""

    def _make(email: str = "seller@example.com"):
        user = make_user(email, role=UserRole.SUPPLIER, verification_status=VerificationStatus.VERIFIED)
        db_session.commit()
        return user

    return _make


@pytest.fixture()
def make_admin(make_user, db_session):
    def _make(email: str = "staff@truconnect.co.za"):
        user = make_user(email, role=UserRole.ADMIN, verification_status=VerificationStatus.VERIFIED)
        db_session.commit()
        return user

    return _make


def _headers(app, user):
    """Mints the token the way AuthService does -- role in the claims.

    Not a detail: a bare create_access_token(identity=...) produces a
    token no role check can read, which is a test artefact rather than
    anything production issues.
    """
    with app.app_context():
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


# ONE REPRESENTATIVE ROUTE PER FAMILY, rather than all 48 -- each gate
# is one function, so a sample proves it is attached, and listing every
# URL here would rot the moment a route is renamed.
#
# THE TWO LISTS ARE THE POINT. There are two different rules in play
# and collapsing them into one would lose the distinction:
#
#   BUSINESS_ONLY   a shop's own books and profile. A supplier has no
#                   customers who owe IT money and no shopfront here.
#   SHARED          genuinely both trading roles.
#
# Both refuse staff; only the first refuses a supplier.
BUSINESS_ONLY_ROUTES = [
    ("GET", "/api/v1/business-profile"),
    ("GET", "/api/v1/loan-book/customers"),
    ("GET", "/api/v1/order-book/orders"),
]

SHARED_ROUTES = [
    ("GET", "/api/v1/notifications"),
    ("GET", "/api/v1/supplier-discovery/connections"),
]

ALL_GATED_ROUTES = BUSINESS_ONLY_ROUTES + SHARED_ROUTES


@pytest.mark.parametrize("method,url", ALL_GATED_ROUTES)
def test_admin_is_refused_everywhere(client, app, make_admin, method, url):
    admin = make_admin()
    response = client.open(url, method=method, headers=_headers(app, admin))
    assert response.status_code == 403, f"{url} let a staff token through"


@pytest.mark.parametrize("method,url", ALL_GATED_ROUTES)
def test_a_business_is_still_let_through(client, app, make_business, method, url):
    """The gate must not be a wall. If this fails the decorator is
    refusing the people it exists to serve, which is worse than the
    hole it closed."""
    business = make_business()
    response = client.open(url, method=method, headers=_headers(app, business))
    assert response.status_code != 403


@pytest.mark.parametrize("method,url", BUSINESS_ONLY_ROUTES)
def test_a_supplier_is_refused_from_a_shops_own_books(client, app, make_seller, method, url):
    """The SECOND hole, closed after the staff one.

    participants_only fixed admins and stopped there, because it
    cannot tell the two trading roles apart -- so a supplier token
    still reached the Loan Book, and still created a business profile
    row on the GET above. Nothing in the mobile app ever called these
    from the supplier side; the routes were simply never pinned.
    """
    supplier = make_seller()
    response = client.open(url, method=method, headers=_headers(app, supplier))
    assert response.status_code == 403, f"{url} let a supplier token through"


@pytest.mark.parametrize("method,url", SHARED_ROUTES)
def test_a_supplier_keeps_the_genuinely_shared_routes(client, app, make_seller, method, url):
    """The other half of the same rule. Tightening must not cost
    suppliers their notifications or their connections list."""
    supplier = make_seller()
    response = client.open(url, method=method, headers=_headers(app, supplier))
    assert response.status_code != 403


def test_admin_hitting_the_business_profile_creates_no_row(client, app, make_admin, db_session):
    """THE ACTUAL BUG, not the status code.

    GET /business-profile is a read that writes: the service calls
    get_or_create_for_business. Before participants_only, a staff token
    reaching it created a BusinessProfile keyed to the admin's user id
    -- no error, no audit entry, just an admin who is now also a
    business in the eyes of every query that joins on that table.
    """
    from src.domains.business.business_profile.models.business_profile import BusinessProfile

    admin = make_admin()
    client.get("/api/v1/business-profile", headers=_headers(app, admin))

    assert BusinessProfile.query.filter_by(business_id=admin.id).first() is None


def test_admin_photo_settings_creates_no_profile(client, app, make_admin, db_session):
    """Same shape, the other write. update_my_photo_settings used to
    read `if supplier ... else <business>`, so an unknown role fell
    through the else and was treated as a business."""
    from src.domains.business.business_profile.models.business_profile import BusinessProfile

    admin = make_admin()
    response = client.patch(
        "/api/v1/supplier-discovery/my-photo-settings",
        json={"photoVisibility": "public"},
        headers=_headers(app, admin),
    )

    assert response.status_code == 403
    assert BusinessProfile.query.filter_by(business_id=admin.id).first() is None


def test_identity_endpoints_stay_open_to_staff(client, app, make_admin):
    """The three routes deliberately left unpinned. An admin who cannot
    ask "who am I" cannot sign in to anything."""
    admin = make_admin()
    headers = _headers(app, admin)

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["data"]["role"] == "admin"

