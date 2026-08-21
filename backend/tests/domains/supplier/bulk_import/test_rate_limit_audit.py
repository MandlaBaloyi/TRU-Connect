"""
Bulk Import's own rate-limit + audit coverage, same shape as
products/inventory's own equivalents -- proves the mapping actually
fires end-to-end, not just present in the dict.
"""
from __future__ import annotations

import io

from flask_jwt_extended import create_access_token

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.shared.audit.audit_types import AuditEventName


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def test_submit_import_rate_limit_is_recorded_in_audit_trail(
    client, db_session, monkeypatch, make_supplier, make_supplier_profile
):
    """BULK_IMPORT_SUBMIT policy is "5 per hour" -- 6 calls guarantees
    the 6th is over the limit. Enqueue is patched to run synchronously
    so each request completes fully before the next, matching how the
    limiter counts real completed requests."""
    monkeypatch.setattr("src.shared.queue.queue.enqueue", lambda job: job())

    supplier = make_supplier()
    make_supplier_profile(supplier)
    token = _token_for(supplier, "supplier")
    csv_bytes = b"name,category,price,unit\nBread,Bakery,19.99,Each\n"

    last_response = None
    for _ in range(6):
        last_response = client.post(
            "/api/v1/supplier-discovery/imports",
            data={"spreadsheet": (io.BytesIO(csv_bytes), "products.csv")},
            content_type="multipart/form-data",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert last_response.status_code == 429

    record = (
        AuditEventRecord.query.filter_by(event_name=AuditEventName.BULK_IMPORT_SUBMIT_RATE_LIMITED.value)
        .order_by(AuditEventRecord.timestamp.desc())
        .first()
    )
    assert record is not None
    assert record.endpoint == "bulk_import.submit_import"
    assert record.user_id == supplier.id
