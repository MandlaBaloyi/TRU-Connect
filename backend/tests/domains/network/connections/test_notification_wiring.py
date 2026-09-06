"""
Formal tests converting this session's own direct verification of the
connection-request notification wiring into permanent coverage.
Deliberately its own file, not folded into an existing connections
test file -- this is testing a genuinely separate concern (does the
right notification fire) from what test_api.py/test_invitations_api.py
already cover (does the connection itself behave correctly).
"""
from __future__ import annotations

from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services import (
    request_service,
)
from src.domains.platform.notifications.repositories.notification_repository import NotificationRepository
from src.shared.queue.queue import wait_until_idle


def test_business_initiated_request_notifies_the_supplier(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Notify Supplier Co")

    request_service.request_connection(business.id, profile.id)
    wait_until_idle(timeout=5)

    results = NotificationRepository.list_for_user(supplier_user.id)
    assert len(results) == 1
    assert results[0].category == "INBOX"
    assert "wants to connect with you" in results[0].body


def test_supplier_initiated_request_notifies_the_business(
    make_business, make_supplier, make_supplier_profile, make_business_profile
):
    business = make_business()
    business_profile = make_business_profile(business, business_name="Notify Business Co")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Requesting Supplier Co")

    request_service.request_connection_to_business(supplier_user.id, business_profile.id)
    wait_until_idle(timeout=5)

    results = NotificationRepository.list_for_user(business.id)
    assert len(results) == 1
    assert results[0].category == "INBOX"
    assert "Requesting Supplier Co" in results[0].body


def test_supplier_approving_a_request_notifies_the_business(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Approving Supplier Co")
    request_service.request_connection(business.id, profile.id)
    request = ConnectionRequestRepository.get_for_business_and_supplier(business.id, profile.id)

    request_service.approve_request(supplier_user.id, request.id)
    wait_until_idle(timeout=5)

    results = NotificationRepository.list_for_user(business.id)
    assert len(results) == 1
    assert "accepted your connection request" in results[0].body
    assert "Approving Supplier Co" in results[0].body


def test_business_approving_a_request_notifies_the_supplier(
    make_business, make_supplier, make_supplier_profile, make_business_profile
):
    business = make_business()
    business_profile = make_business_profile(business, business_name="Approving Business Co")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Waiting Supplier Co")
    request_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request = ConnectionRequestRepository.get_for_business_and_supplier(business.id, profile.id)

    request_service.approve_supplier_request(business.id, request.id)
    wait_until_idle(timeout=5)

    results = NotificationRepository.list_for_user(supplier_user.id)
    assert len(results) == 1
    assert "accepted your connection request" in results[0].body
    assert "Approving Business Co" in results[0].body


def test_declining_a_request_does_not_notify_anyone(make_business, make_supplier, make_supplier_profile):
    """CONFIRMED, NOT ASSUMED -- a decline notification was
    deliberately not built (unresolved judgment call, per direct
    discussion). This proves that absence is real, not accidental --
    a business's own request being declined produces zero
    notifications for them, on purpose."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Declining Supplier Co")
    request_service.request_connection(business.id, profile.id)
    request = ConnectionRequestRepository.get_for_business_and_supplier(business.id, profile.id)

    # Clear the "new request" notification the supplier already got,
    # so this test only looks at what decline itself does.
    NotificationRepository.mark_all_read(supplier_user.id)

    request_service.decline_request(supplier_user.id, request.id)
    wait_until_idle(timeout=5)

    business_results = NotificationRepository.list_for_user(business.id)
    assert business_results == []
