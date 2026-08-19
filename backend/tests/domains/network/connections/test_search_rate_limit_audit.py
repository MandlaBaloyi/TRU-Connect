"""
Regression coverage for a real gap found during codebase review:
RATE_LIMIT_AUDIT_EVENTS (connections/rate_limit/policies.py) mapped
"connections.search" (business -> supplier) to an audit event, but
never mapped "connections.search_businesses" (supplier -> business,
Find Business) to one. The 429 response itself always fired correctly
either way -- this is specifically about whether the security audit
trail records the violation, per responses.py's
_AUDIT_EVENT_REGISTRY.get(request.endpoint) lookup.

Neither direction had ANY test exercising this path end-to-end before
this file -- these are new tests, not fixes to existing failing ones.

Both endpoints are hit real-HTTP, through the actual flask-limiter
instance (in-memory storage -- see limiter.py's own docstring), rather
than calling handle_rate_limit_exceeded directly, so this also proves
the decorator + endpoint-name wiring is correct, not just the mapping
dict in isolation.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.shared.audit.audit_types import AuditEventName


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def _exhaust_search_limit(client, path: str, token: str) -> None:
    """SEARCH policy is "30 per minute" (rate_limit/policies.py) --
    31 calls guarantees the 31st is over the limit regardless of any
    per-request jitter."""
    last_response = None
    for _ in range(31):
        last_response = client.get(
            path,
            headers={"Authorization": f"Bearer {token}"},
        )
    assert last_response.status_code == 429, (
        f"expected the 31st call to {path} to be rate-limited, got {last_response.status_code}"
    )


class TestBusinessSearchRateLimitAudit:
    """connections.search -- the mapping that already existed. Kept
    here as a same-shape counterpart to the supplier-side test below,
    since neither direction had HTTP-level audit coverage before."""

    def test_rate_limited_search_is_recorded_in_audit_trail(
        self, client, db_session, make_business, make_supplier, make_supplier_profile
    ):
        business = make_business()
        supplier_user = make_supplier()
        make_supplier_profile(supplier_user, business_name="Audit Test Wholesale")
        token = _token_for(business, "business")

        _exhaust_search_limit(client, "/api/v1/supplier-discovery/search?q=Audit", token)

        record = (
            AuditEventRecord.query.filter_by(event_name=AuditEventName.SUPPLIER_SEARCH_RATE_LIMITED.value)
            .order_by(AuditEventRecord.timestamp.desc())
            .first()
        )
        assert record is not None
        assert record.endpoint == "connections.search"
        assert record.user_id == business.id


class TestSupplierSearchRateLimitAudit:
    """connections.search_businesses -- the endpoint that was silently
    unmapped. Before the fix, this test fails at the AuditEventRecord
    lookup: the 429 still fires (protection works), but no row is ever
    written, because responses.py's handler finds nothing for this
    endpoint in _AUDIT_EVENT_REGISTRY and skips logging entirely."""

    def test_rate_limited_search_is_recorded_in_audit_trail(
        self, client, db_session, make_supplier, make_business, make_business_profile
    ):
        supplier_user = make_supplier()
        business_user = make_business()
        make_business_profile(business_user, business_name="Audit Test Business")
        token = _token_for(supplier_user, "supplier")

        _exhaust_search_limit(client, "/api/v1/supplier-discovery/businesses/search?q=Audit", token)

        record = (
            AuditEventRecord.query.filter_by(event_name=AuditEventName.BUSINESS_SEARCH_RATE_LIMITED.value)
            .order_by(AuditEventRecord.timestamp.desc())
            .first()
        )
        assert record is not None
        assert record.endpoint == "connections.search_businesses"
        assert record.user_id == supplier_user.id
