"""RBAC field-group serialization -- unchanged logic, import path moved
to security.audit.schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from src.domains.security.audit.schemas.audit_schemas import FieldGroup, serialize


def _record():
    return SimpleNamespace(
        id="abc-123", timestamp=datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc),
        domain="auth", module="auth_service", event_name="auth.login_failed",
        category="authentication", severity="medium", status="failure",
        failure_reason="invalid_credentials", actor_type="user", user_id="user-1",
        email="power@example.com", role="business", tenant_id=None,
        ip_address="198.51.100.7", user_agent="Mozilla/5.0 Chrome/120",
        browser="Chrome", operating_system="Windows", platform="web",
        device_id="device-xyz", session_id="sess-1", correlation_id="corr-1",
        request_id="req-1", http_method="POST", endpoint="/api/v1/auth/login",
        http_status_code=401, event_metadata={"attempt": 3},
    )


def test_basic_group_masks_email():
    out = serialize(_record(), FieldGroup.BASIC)
    assert out["email"] != "power@example.com"


def test_investigator_group_reveals_email():
    out = serialize(_record(), FieldGroup.INVESTIGATOR)
    assert out["email"] == "power@example.com"
