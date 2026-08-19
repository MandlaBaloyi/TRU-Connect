"""
Product repository -- ONLY talks to SQLAlchemy, no business rules
(same rule as every other repository in this codebase). Grown from the
deliberately minimal version that only needed create/list/count for
the ordering gate; now the full CRUD + bulk surface the real Products
feature needs.

KNOWN LIMITATION, FLAGGED NOT HIDDEN: list_for_supplier has no
pagination. The frontend doesn't send page/limit params today (its
mock API returns everything unpaginated), so building server-side
pagination now would mean either the frontend silently never sees
page 2, or building pagination UI nobody asked for yet in this phase.
Real pagination is a genuine follow-up once a supplier's catalogue
size makes it necessary -- the supplier_profile_id+is_archived index
this table already has is exactly what a future LIMIT/OFFSET (or
keyset) query would use, so adding it later doesn't require an index
migration, only a repository/route change.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.products.models.product import Product, ProductCategory, ProductUnit
from src.extensions import db


class ProductRepository:
    @staticmethod
    def create(
        supplier_profile_id: str | UUID,
        name: str,
        category: ProductCategory,
        price_cents: int,
        selling_unit: ProductUnit,
        unit_quantity: Optional[int] = None,
        unit_measure: Optional[ProductUnit] = None,
    ) -> Product:
        product = Product(
            supplier_profile_id=supplier_profile_id,
            name=name,
            category=category,
            price_cents=price_cents,
            selling_unit=selling_unit,
            unit_quantity=unit_quantity,
            unit_measure=unit_measure,
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def get_by_id(product_id: str | UUID) -> Optional[Product]:
        return Product.query.filter_by(id=product_id, is_deleted=False).first()

    @staticmethod
    def get_by_id_and_supplier(product_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[Product]:
        """Ownership-scoped lookup -- used by every mutation (update,
        archive, bulk actions) so a supplier can never affect a product
        that isn't theirs, same IDOR-safety shape as every other
        domain's own get_by_id_and_<owner> repository method."""
        return Product.query.filter_by(
            id=product_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def list_for_supplier(
        supplier_profile_id: str | UUID,
        include_archived: bool = False,
        search_term: Optional[str] = None,
    ) -> List[Product]:
        query = Product.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False)
        if not include_archived:
            query = query.filter_by(is_archived=False)
        if search_term:
            # Substring, not prefix -- this is a supplier browsing their
            # OWN catalogue, not the public supplier-search endpoint
            # (connections_service.search_suppliers), which deliberately
            # uses prefix-only matching for the enumeration-vector
            # reasons documented there. That reasoning doesn't apply to
            # a supplier searching their own products.
            query = query.filter(Product.name.ilike(f"%{search_term}%"))
        return query.order_by(Product.created_at.desc()).all()

    @staticmethod
    def count_for_supplier(supplier_profile_id: str | UUID) -> int:
        """The ordering gate's own question, answered directly rather
        than via len(list_for_supplier(...)) -- a COUNT query, not a
        full row fetch, for something that will get called on every
        single ordering-eligibility check. Deliberately counts ALL
        non-deleted products regardless of archive state, matching the
        pre-existing behaviour -- worth a deliberate look once Orders
        is built, since an archived product arguably shouldn't count.
        """
        return Product.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False).count()

    @staticmethod
    def update(
        product: Product,
        name: str,
        category: ProductCategory,
        price_cents: int,
        selling_unit: ProductUnit,
    ) -> Product:
        product.name = name
        product.category = category
        product.price_cents = price_cents
        product.selling_unit = selling_unit
        db.session.commit()
        return product

    @staticmethod
    def archive(product: Product) -> Product:
        product.is_archived = True
        db.session.commit()
        return product

    @staticmethod
    def bulk_adjust_price(products: List[Product], apply_fn) -> List[Product]:
        """`apply_fn(current_price_cents: int) -> int` -- the actual
        percentage/fixed math lives in the SERVICE layer (same
        "repository has no business rules" line every other repository
        in this codebase draws); this method only knows how to apply an
        already-computed function to a batch and commit once."""
        for product in products:
            product.price_cents = apply_fn(product.price_cents)
        db.session.commit()
        return products

    @staticmethod
    def bulk_archive(products: List[Product]) -> List[Product]:
        for product in products:
            product.is_archived = True
        db.session.commit()
        return products

    @staticmethod
    def list_by_ids_and_supplier(product_ids: List[str | UUID], supplier_profile_id: str | UUID) -> List[Product]:
        """Used by both bulk endpoints -- fetches only the rows this
        supplier actually owns among the requested ids, so a bulk
        request that includes someone else's product id silently
        excludes it rather than erroring the whole batch or, worse,
        acting on it."""
        return Product.query.filter(
            Product.id.in_(product_ids),
            Product.supplier_profile_id == supplier_profile_id,
            Product.is_deleted.is_(False),
        ).all()
