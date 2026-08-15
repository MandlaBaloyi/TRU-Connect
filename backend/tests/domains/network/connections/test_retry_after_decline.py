"""
Tests for retry-after-decline (MAX_CONNECTION_RETRY_PER_DAY/_PER_WEEK).
Real Postgres, real datetime windows -- retry_history entries are
inserted directly with controlled timestamps to make the day/week
boundary tests deterministic rather than depending on real wall-clock
timing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domains.network.connections.models.connection_request import (
    ConnectionInitiatorRole,
    ConnectionRequest,
    ConnectionRequestStatus,
)
from src.domains.network.connections.services import connections_service
from src.domains.network.connections.services.errors import RetryLimitExceededError


def _decline(business, supplier_profile):
    connections_service.request_connection(business.id, supplier_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=supplier_profile.id).first()
    request.status = ConnectionRequestStatus.DECLINED
    from src.extensions import db

    db.session.commit()
    return request


def test_first_retry_after_decline_succeeds(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Retry Test Co")
    _decline(business, profile)

    result = connections_service.request_connection(business.id, profile.id)

    assert result["connectionStatus"] == "PENDING"


def test_retry_records_a_timestamp_in_retry_history(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="History Test Co")
    _decline(business, profile)

    connections_service.request_connection(business.id, profile.id)

    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    assert len(request.retry_history) == 1


def test_second_retry_same_day_exceeds_daily_limit(make_business, make_supplier, make_supplier_profile):
    """MAX_CONNECTION_RETRY_PER_DAY defaults to 1 -- a second retry
    within the same day must be blocked."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Daily Limit Co")
    _decline(business, profile)

    connections_service.request_connection(business.id, profile.id)  # 1st retry — succeeds
    # Decline it again so there's something to retry a second time.
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    request.status = ConnectionRequestStatus.DECLINED
    from src.extensions import db

    db.session.commit()

    with pytest.raises(RetryLimitExceededError) as exc_info:
        connections_service.request_connection(business.id, profile.id)  # 2nd retry, same day — blocked

    assert exc_info.value.data is not None
    assert "nextRetryAt" in exc_info.value.data


def test_retry_allowed_again_after_a_day_passes(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Next Day Co")
    request = _decline(business, profile)

    # Backdate a retry attempt to 2 days ago -- outside the daily
    # window, still inside the weekly one.
    from src.extensions import db

    request.retry_history = [datetime.now(timezone.utc) - timedelta(days=2)]
    db.session.commit()

    result = connections_service.request_connection(business.id, profile.id)
    assert result["connectionStatus"] == "PENDING"


def test_weekly_limit_blocks_even_when_daily_would_allow(make_business, make_supplier, make_supplier_profile):
    """MAX_CONNECTION_RETRY_PER_WEEK defaults to 3. Three retries
    spread across different days (each individually clear of the
    daily limit) must still be blocked by the weekly cap."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Weekly Limit Co")
    request = _decline(business, profile)

    from src.extensions import db

    now = datetime.now(timezone.utc)
    # Three attempts, each more than a day apart from the others, all within the last week.
    request.retry_history = [now - timedelta(days=5), now - timedelta(days=3), now - timedelta(days=1, hours=2)]
    db.session.commit()

    with pytest.raises(RetryLimitExceededError):
        connections_service.request_connection(business.id, profile.id)


def test_retry_no_longer_counts_once_outside_the_weekly_window(make_business, make_supplier, make_supplier_profile):
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Old History Co")
    request = _decline(business, profile)

    from src.extensions import db

    now = datetime.now(timezone.utc)
    # All three attempts are OLDER than a week -- none should count
    # against either limit.
    request.retry_history = [now - timedelta(days=20), now - timedelta(days=15), now - timedelta(days=10)]
    db.session.commit()

    result = connections_service.request_connection(business.id, profile.id)
    assert result["connectionStatus"] == "PENDING"


def test_reverse_direction_retry_also_enforced(make_business, make_supplier, make_supplier_profile, make_business_profile):
    """The same limits apply identically to the supplier-initiated
    direction (Find Business), not just business-initiated."""
    business = make_business()
    business_profile = make_business_profile(business, business_name="Reverse Retry Co")
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Reverse Retry Supplier")

    connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    request = ConnectionRequest.query.filter_by(business_id=business.id, supplier_profile_id=profile.id).first()
    request.status = ConnectionRequestStatus.DECLINED
    from src.extensions import db

    db.session.commit()

    result = connections_service.request_connection_to_business(supplier_user.id, business_profile.id)
    assert result["connectionStatus"] == "PENDING"


def test_pending_and_active_requests_remain_fully_idempotent(make_business, make_supplier, make_supplier_profile):
    """Only DECLINED goes through the retry-limit machinery — a
    PENDING or ACTIVE request must remain simply idempotent, exactly
    as before this feature existed."""
    business = make_business()
    supplier_user = make_supplier()
    profile = make_supplier_profile(supplier_user, business_name="Idempotent Co")

    first = connections_service.request_connection(business.id, profile.id)
    second = connections_service.request_connection(business.id, profile.id)

    assert first["connectionStatus"] == "PENDING"
    assert second["connectionStatus"] == "PENDING"
    assert ConnectionRequest.query.count() == 1
