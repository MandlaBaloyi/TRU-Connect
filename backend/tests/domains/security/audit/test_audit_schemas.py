"""
RBAC field-group serialization — proves sensitive fields are actually
withheld at lower tiers, before any route exists to depend on it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from src.domains.security.schemas.audit_schemas import FieldGroup, serialize


def _record():
    return SimpleNamespace(
        id="abc-123",
        timestamp=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
        domain="auth",
        module="auth_service",
        event_name="auth.login_failed",
        category="authentication",
        severity="medium",
        status="failure",
        failure_reason="invalid_credentials",
        actor_type="user",
        user_id="user-1",
        email="power@example.com",
        role="business",
        tenant_id=None,
        ip_address="198.51.100.7",
        user_agent="Mozilla/5.0 Chrome/120",
        browser="Chrome",
        operating_system="Windows",
        platform="web",
        device_id="device-xyz",
        session_id="sess-1",
        correlation_id="corr-1",
        request_id="req-1",
        http_method="POST",
        endpoint="/api/v1/auth/login",
        http_status_code=401,
        event_metadata={"attempt": 3},
    )


def test_basic_group_masks_email_and_hides_network_detail():
    out = serialize(_record(), FieldGroup.BASIC)

    assert out["event_name"] == "auth.login_failed"
    assert out["email"] != "power@example.com"     # masked at this tier
    assert "ip_address" not in out
    assert "user_agent" not in out
    assert "device_id" not in out
    assert "metadata" not in out


def test_investigator_group_reveals_email_and_network_detail():
    out = serialize(_record(), FieldGroup.INVESTIGATOR)

    assert out["email"] == "power@example.com"
    assert out["ip_address"] == "198.51.100.7"
    assert out["correlation_id"] == "corr-1"
    # still withheld at this tier
    assert "user_agent" not in out
    assert "device_id" not in out


def test_full_group_includes_fingerprinting_fields_and_metadata():
    out = serialize(_record(), FieldGroup.FULL)

    assert out["user_agent"] == "Mozilla/5.0 Chrome/120"
    assert out["device_id"] == "device-xyz"
    assert out["metadata"] == {"attempt": 3}


def test_timestamp_is_iso_serialized():
    out = serialize(_record(), FieldGroup.BASIC)
    assert out["timestamp"] == "2026-08-02T12:00:00+00:00"
