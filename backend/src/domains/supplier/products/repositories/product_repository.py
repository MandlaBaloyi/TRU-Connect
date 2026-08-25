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
        sku: str,
        product_code: str,
        unit_quantity: Optional[int] = None,
        unit_measure: Optional[ProductUnit] = None,
        description: Optional[str] = None,
        compare_at_price_cents: Optional[int] = None,
    ) -> Product:
        product = Product(
            supplier_profile_id=supplier_profile_id,
            name=name,
            category=category,
            price_cents=price_cents,
            selling_unit=selling_unit,
            sku=sku,
            product_code=product_code,
            unit_quantity=unit_quantity,
            unit_measure=unit_measure,
            description=description,
            compare_at_price_cents=compare_at_price_cents,
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def product_code_exists(product_code: str) -> bool:
        """The generator's own collision check (see
        algorithms/product_code_generator.py) -- includes soft-deleted
        rows on purpose: a product_code must never be reissued to a
        different product just because the original was deleted, same
        "never reused" discipline as the SKU sequence counter."""
        return db.session.query(
            Product.query.filter_by(product_code=product_code).exists()
        ).scalar()

    @staticmethod
    def sku_exists_for_supplier(supplier_profile_id: str | UUID, sku: str) -> bool:
        """Used to validate a supplier's own CUSTOM-typed SKU before
        save -- auto-generated SKUs can never collide (see
        algorithms/sku_generator.py's own atomic counter), but a
        supplier typing one by hand genuinely could accidentally repeat
        an existing one."""
        return db.session.query(
            Product.query.filter_by(supplier_profile_id=supplier_profile_id, sku=sku, is_deleted=False).exists()
        ).scalar()

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
        is_archived: Optional[bool] = False,
        search_term: Optional[str] = None,
    ) -> List[Product]:
        # REAL BUG FOUND DURING DEVICE TESTING: this used to be a plain
        # `include_archived: bool`. include_archived=True only ever
        # meant "stop excluding archived rows" -- it never meant "show
        # ONLY archived rows." Selecting the Archived filter tab on the
        # real app set include_archived=True and got back EVERY
        # product, active and archived mixed, because nothing ever
        # excluded the active ones. Fixed with a genuine three-state
        # filter matching what the is_archived COLUMN itself means:
        #   is_archived=False (default) -> active only, the normal browsing view
        #   is_archived=True            -> archived only, the Archived tab
        #   is_archived=None            -> no filter, both together (no
        #                                  real caller needs this today,
        #                                  kept for a genuine future need
        #                                  rather than removed outright)
        query = Product.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False)
        if is_archived is not None:
            query = query.filter_by(is_archived=is_archived)
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
        sku: Optional[str] = None,
        description: Optional[str] = None,
        compare_at_price_cents: Optional[int] = None,
    ) -> Product:
        product.name = name
        product.category = category
        product.price_cents = price_cents
        product.selling_unit = selling_unit
        # product_code is DELIBERATELY never touched here -- see its
        # own column docstring on product.py. sku IS editable; None is
        # never passed by the service layer (it always resolves to the
        # product's existing sku first), but kept Optional here for
        # defensive correctness rather than assuming every future
        # caller gets that right.
        if sku is not None:
            product.sku = sku
        product.description = description
        product.compare_at_price_cents = compare_at_price_cents
        db.session.commit()
        return product

    @staticmethod
    def archive(product: Product) -> Product:
        product.is_archived = True
        db.session.commit()
        return product

    @staticmethod
    def unarchive(product: Product) -> Product:
        product.is_archived = False
        db.session.commit()
        return product

    @staticmethod
    def soft_delete(product: Product) -> Product:
        # BaseModel's own real, ready-to-use soft_delete() -- sets
        # is_deleted=True and deleted_at, never actually removes the
        # row. Every existing query in this repository already filters
        # is_deleted=False, so this alone is what makes a "deleted"
        # product vanish from every screen while the row itself, and
        # everything else pointing at it (Inventory, ProductMedia),
        # stays completely intact for future analysis.
        product.soft_delete()
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
    def bulk_set_compare_at_price(products: List[Product], compute_fn) -> List[Product]:
        """`compute_fn(current_price_cents: int) -> int` -- the actual
        discount-percentage math lives in the SERVICE layer, same
        "repository has no business rules" split as bulk_adjust_price
        just above. Sets compare_at_price_cents FROM each product's own
        CURRENT price_cents -- price_cents itself is never touched here,
        matching the real "Set Discount" feature's own point: mark
        products on sale without changing what they actually sell for.

        ALL-OR-NOTHING, ENFORCED HERE, NOT ASSUMED FROM THE CALLER'S
        OWN SESSION LIFECYCLE -- a real bug found while writing this
        feature's own tests: if compute_fn raises partway through the
        loop, the in-memory attribute assignments already made to
        EARLIER products in the batch stayed dirty on those ORM
        objects even though db.session.commit() was never reached --
        visible to anything sharing the same session (a test's own
        persistent session, in particular) even though nothing was
        ever actually persisted. Relying on Flask's own end-of-request
        session teardown to implicitly roll this back was a real, if
        usually-invisible, gap -- explicitly rolling back here
        guarantees the property regardless of the caller's own session
        lifecycle."""
        try:
            for product in products:
                product.compare_at_price_cents = compute_fn(product.price_cents)
        except Exception:
            db.session.rollback()
            raise
        db.session.commit()
        return products

    @staticmethod
    def bulk_archive(products: List[Product]) -> List[Product]:
        for product in products:
            product.is_archived = True
        db.session.commit()
        return products

    @staticmethod
    def bulk_unarchive(products: List[Product]) -> List[Product]:
        for product in products:
            product.is_archived = False
        db.session.commit()
        return products

    @staticmethod
    def bulk_soft_delete(products: List[Product]) -> List[Product]:
        for product in products:
            product.soft_delete()
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
