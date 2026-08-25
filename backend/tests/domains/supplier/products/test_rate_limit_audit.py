"""
Products' own rate-limit + audit coverage -- proves the mapping in
rate_limit/policies.py's RATE_LIMIT_AUDIT_EVENTS actually works
end-to-end through the real flask-limiter instance, not just that the
dict entry is present. Same shape as network/connections/
test_search_rate_limit_audit.py, written specifically because that
file exists as a regression test for a mapping that WAS missing --
Products' own mapping is written and tested together from the start,
per that lesson.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.shared.audit.event_types.supplier import SupplierAuditEvent


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def test_create_product_rate_limit_is_recorded_in_audit_trail(client, db_session, make_supplier, make_supplier_profile):
    """PRODUCT_CREATE policy is "30 per minute" -- 31 calls guarantees
    the 31st is over the limit regardless of any per-request jitter."""
    supplier = make_supplier()
    make_supplier_profile(supplier)
    token = _token_for(supplier, "supplier")
    payload = {"name": "Bread", "category": "BAKERY", "price_cents": 100, "selling_unit": "EACH"}

    last_response = None
    for _ in range(31):
        last_response = client.post(
            "/api/v1/supplier-discovery/products",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert last_response.status_code == 429

    record = (
        AuditEventRecord.query.filter_by(event_name=SupplierAuditEvent.PRODUCT_CREATE_RATE_LIMITED.value)
        .order_by(AuditEventRecord.timestamp.desc())
        .first()
    )
    assert record is not None
    assert record.endpoint == "products.create_product"
    assert record.user_id == supplier.id


def test_bulk_archive_rate_limit_is_recorded_in_audit_trail(client, db_session, make_supplier, make_supplier_profile):
    """PRODUCT_BULK_ACTION policy is "10 per minute" -- 11 calls
    guarantees the 11th is over the limit."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    product = ProductRepository.create(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH,
        sku=generate_sku(profile.id), product_code=generate_product_code(),
    )
    token = _token_for(supplier, "supplier")
    payload = {"product_ids": [str(product.id)]}

    last_response = None
    for _ in range(11):
        last_response = client.post(
            "/api/v1/supplier-discovery/products/bulk/archive",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert last_response.status_code == 429

    record = (
        AuditEventRecord.query.filter_by(event_name=SupplierAuditEvent.PRODUCT_BULK_ACTION_RATE_LIMITED.value)
        .order_by(AuditEventRecord.timestamp.desc())
        .first()
    )
    assert record is not None
    assert record.endpoint == "products.bulk_archive"
    assert record.user_id == supplier.id
