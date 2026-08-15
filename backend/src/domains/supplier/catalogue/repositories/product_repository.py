"""
Product repository -- ONLY talks to SQLAlchemy, no business rules
(same rule as every other repository in this codebase). Deliberately
minimal, matching product.py's own docstring: just enough to answer
"does this supplier have any real products" for the ordering gate, and
to list them for a real (even if minimal) "view products" screen.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.domains.supplier.catalogue.models.product import Product
from src.extensions import db


class ProductRepository:
    @staticmethod
    def create(supplier_profile_id: str | UUID, name: str) -> Product:
        product = Product(supplier_profile_id=supplier_profile_id, name=name)
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def list_for_supplier(supplier_profile_id: str | UUID) -> List[Product]:
        return (
            Product.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False)
            .order_by(Product.created_at.desc())
            .all()
        )

    @staticmethod
    def count_for_supplier(supplier_profile_id: str | UUID) -> int:
        """The ordering gate's own question, answered directly rather
        than via len(list_for_supplier(...)) -- a COUNT query, not a
        full row fetch, for something that will get called on every
        single ordering-eligibility check."""
        return Product.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False).count()
