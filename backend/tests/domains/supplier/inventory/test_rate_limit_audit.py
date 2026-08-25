"""
Inventory's own rate-limit + audit coverage, same shape as
products/test_rate_limit_audit.py -- proves the mapping actually
fires end-to-end, not just present in the dict.
"""
from __future__ import annotations

from flask_jwt_extended import create_access_token

from src.domains.security.audit.models.audit_event import AuditEventRecord
from src.domains.supplier.products.models.product import ProductCategory, ProductUnit
from src.domains.supplier.products.repositories.product_repository import ProductRepository
from src.shared.audit.event_types.supplier import SupplierAuditEvent


def _token_for(user, role: str) -> str:
    return create_access_token(identity=str(user.id), additional_claims={"role": role})


def test_adjust_stock_rate_limit_is_recorded_in_audit_trail(client, db_session, make_supplier, make_supplier_profile):
    """INVENTORY_ADJUST policy is "20 per minute" -- 21 calls
    guarantees the 21st is over the limit."""
    supplier = make_supplier()
    profile = make_supplier_profile(supplier)
    from src.domains.supplier.products.algorithms.product_code_generator import generate_product_code
    from src.domains.supplier.products.algorithms.sku_generator import generate_sku

    product = ProductRepository.create(
        profile.id, "Bread", ProductCategory.BAKERY, 100, ProductUnit.EACH,
        sku=generate_sku(profile.id), product_code=generate_product_code(),
    )
    token = _token_for(supplier, "supplier")
    payload = {"quantity_delta": 1, "reason": "STOCK_RECEIVED"}

    last_response = None
    for _ in range(21):
        last_response = client.post(
            f"/api/v1/supplier-discovery/inventory/{product.id}/adjust",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert last_response.status_code == 429

    record = (
        AuditEventRecord.query.filter_by(event_name=SupplierAuditEvent.INVENTORY_ADJUST_RATE_LIMITED.value)
        .order_by(AuditEventRecord.timestamp.desc())
        .first()
    )
    assert record is not None
    assert record.endpoint == "inventory.adjust_stock"
    assert record.user_id == supplier.id
