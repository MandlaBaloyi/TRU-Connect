"""
SupplierPinnedProductRepository -- pure SQL, no business rules (the
MAX-6 limit, ownership checks, and archived filtering all live in
pinned_products_service).
"""
from __future__ import annotations

from typing import List, Optional, Set
from uuid import UUID

from src.domains.supplier.supplier_profile.models.supplier_profile_pin import SupplierPinnedProduct
from src.extensions import db


class SupplierPinnedProductRepository:
    @staticmethod
    def list_for_supplier(supplier_profile_id: str | UUID) -> List[SupplierPinnedProduct]:
        return (
            SupplierPinnedProduct.query.filter_by(
                supplier_profile_id=supplier_profile_id, is_deleted=False
            )
            .order_by(SupplierPinnedProduct.pin_order.asc())
            .all()
        )

    @staticmethod
    def list_product_ids(supplier_profile_id: str | UUID) -> Set[UUID]:
        rows = (
            db.session.query(SupplierPinnedProduct.product_id)
            .filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False)
            .all()
        )
        return {row[0] for row in rows}

    @staticmethod
    def get(supplier_profile_id: str | UUID, product_id: str | UUID) -> Optional[SupplierPinnedProduct]:
        return SupplierPinnedProduct.query.filter_by(
            supplier_profile_id=supplier_profile_id, product_id=product_id, is_deleted=False
        ).first()

    @staticmethod
    def count(supplier_profile_id: str | UUID) -> int:
        return SupplierPinnedProduct.query.filter_by(
            supplier_profile_id=supplier_profile_id, is_deleted=False
        ).count()

    @staticmethod
    def max_pin_order(supplier_profile_id: str | UUID) -> int:
        row = (
            db.session.query(db.func.max(SupplierPinnedProduct.pin_order))
            .filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False)
            .scalar()
        )
        return row if row is not None else -1

    @staticmethod
    def add(supplier_profile_id: str | UUID, product_id: str | UUID, pin_order: int) -> SupplierPinnedProduct:
        pin = SupplierPinnedProduct(
            supplier_profile_id=supplier_profile_id, product_id=product_id, pin_order=pin_order
        )
        db.session.add(pin)
        db.session.commit()
        return pin

    @staticmethod
    def remove(pin: SupplierPinnedProduct) -> None:
        pin.soft_delete()
        db.session.commit()
