"""
Product repository -- ONLY talks to SQLAlchemy, no business rules
(same rule as every other repository in this codebase). Grown from the
deliberately minimal version that only needed create/list/count for
the ordering gate; now the full CRUD + bulk surface the real Products
feature needs.

list_for_supplier ITSELF STAYS UNPAGINATED, DELIBERATELY -- it's
shared by the supplier's own Products screen and other callers that
genuinely want the full, unfiltered list; adding pagination directly
to it would force every existing caller to start handling pages it
never asked for. Real server-side pagination exists as its own,
separate method (list_for_supplier_paginated below), built once the
business-facing catalogue view genuinely needed it -- a supplier with
hundreds of products meant one request returning every row at once.
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
            # (connections' discovery_service.search_suppliers), which deliberately
            # uses prefix-only matching for the enumeration-vector
            # reasons documented there. That reasoning doesn't apply to
            # a supplier searching their own products.
            query = query.filter(Product.name.ilike(f"%{search_term}%"))
        return query.order_by(Product.created_at.desc()).all()

    @staticmethod
    def _apply_ranked_sort(query, sort: str, supplier_profile_id: str | UUID):
        """The two COMPUTED orderings, expressed in SQL so they survive
        pagination (see list_for_supplier_paginated's own note).

        RECOMMENDED is the same rule the brand-profile showcase uses
        (storefront/ranking.showcase_sort_key): in stock first, then
        deepest discount, then newest. It replaced NEWEST as the
        catalogue default -- with NEWEST, whatever a supplier uploaded
        most recently led their shop regardless of whether it was in
        stock or worth buying.

        BEST_SELLING counts units actually sold, from CONFIRMED orders
        only: a cart nobody checked out, or an order the supplier
        declined, is not evidence of anything.

        Both LEFT JOIN, never INNER -- a product with no inventory row
        and a product nobody has ever ordered must still appear in the
        catalogue, ranked last rather than dropped. An inner join here
        would silently hide a supplier's newest stock.
        """
        from src.domains.network.orders.models.stock_order import (
            StockOrder,
            StockOrderItem,
            StockOrderStatus,
        )
        from src.domains.supplier.inventory.models.inventory import Inventory

        if sort == "BEST_SELLING":
            sold = (
                db.session.query(
                    StockOrderItem.product_id.label("product_id"),
                    db.func.coalesce(db.func.sum(StockOrderItem.quantity), 0).label("units"),
                )
                .join(StockOrder, StockOrder.id == StockOrderItem.stock_order_id)
                .filter(
                    StockOrder.supplier_profile_id == supplier_profile_id,
                    StockOrder.status == StockOrderStatus.CONFIRMED,
                    StockOrder.is_deleted.is_(False),
                    StockOrderItem.is_deleted.is_(False),
                )
                .group_by(StockOrderItem.product_id)
                .subquery()
            )
            return query.outerjoin(sold, sold.c.product_id == Product.id).order_by(
                db.func.coalesce(sold.c.units, 0).desc(),
                Product.created_at.desc(),
            )

        # RECOMMENDED
        available = (
            db.func.coalesce(Inventory.quantity_on_hand, 0)
            - db.func.coalesce(Inventory.quantity_reserved, 0)
        )
        # Discount as a FRACTION, computed in SQL. NULLIF guards a zero
        # compare-at (division by zero); the outer comparison makes a
        # compare-at at or below the price count as no discount at all,
        # exactly as ranking._discount_fraction does -- stale or
        # mis-entered data must never rank a product UP.
        discount = db.case(
            (
                db.and_(
                    Product.compare_at_price_cents.isnot(None),
                    Product.compare_at_price_cents > Product.price_cents,
                ),
                (Product.compare_at_price_cents - Product.price_cents)
                * 1.0
                / db.func.nullif(Product.compare_at_price_cents, 0),
            ),
            else_=0.0,
        )
        return query.outerjoin(Inventory, Inventory.product_id == Product.id).order_by(
            (available > 0).desc(),
            discount.desc(),
            Product.created_at.desc(),
        )

    @staticmethod
    def list_for_supplier_paginated(
        supplier_profile_id: str | UUID,
        page: int,
        limit: int,
        sort: str,
        category: Optional[str],
        search_term: Optional[str] = None,
    ) -> tuple[List[Product], int]:
        """A SEPARATE method from list_for_supplier above, deliberately
        -- that one is shared by the supplier's own Products screen and
        other callers that want the full, unpaginated list; adding
        pagination directly to it would force every existing caller to
        start handling pages it never asked for. This one exists
        specifically for the business-facing catalogue view
        (connections' catalog_service.list_supplier_products), where a
        supplier with hundreds of products genuinely needs to be
        fetched a page at a time, not all at once -- REAL "protect the
        API, and scale" concern, not a cosmetic one: without this, one
        request for a large catalogue means one query returning
        potentially hundreds of rows (and hundreds of image-URL
        resolutions alongside them).

        Returns (products for this one page, total count matching the
        filter) -- the total is computed from the SAME filtered query,
        BEFORE pagination is applied, so the frontend can render the
        real number of pages regardless of which page it's currently
        showing.

        Sort/category validation happens in the SERVICE layer, not
        here -- same "repository has no business rules" discipline
        already established throughout this codebase.

        EVERY SORT IS APPLIED IN SQL, INCLUDING THE COMPUTED ONES.
        RECOMMENDED and BEST_SELLING could have been expressed far more
        readably as a Python sort over the enriched product dicts (the
        showcase does exactly that, see storefront/ranking.py) -- but
        that only works when you have the WHOLE list. Here the list is
        paginated, and sorting in Python after the fact would sort each
        page WITHIN ITSELF: page 1 would hold an arbitrary 20 products
        neatly ordered, while the genuinely best-selling item sat on
        page 3. Ranking has to happen before LIMIT/OFFSET, which means
        it has to happen in the database.
        """
        from src.domains.supplier.products.models.product import ProductCategory

        query = Product.query.filter_by(
            supplier_profile_id=supplier_profile_id, is_deleted=False, is_archived=False
        )
        if category is not None:
            query = query.filter_by(category=ProductCategory(category))

        if search_term:
            # Substring, not prefix -- a business hunting inside ONE
            # supplier's catalogue they already have a relationship with
            # is not the public discovery search, so file.txt §4's
            # enumeration concern (prefix-only, see
            # search_by_name_prefix) genuinely doesn't apply. Matching
            # "cola" against "Coca-Cola 500ml" is the whole point.
            from src.shared.validation.identifiers import escape_like_pattern

            pattern = f"%{escape_like_pattern(search_term.strip())}%"
            query = query.filter(Product.name.ilike(pattern, escape="\\"))

        total_count = query.count()

        if sort in ("RECOMMENDED", "BEST_SELLING"):
            query = ProductRepository._apply_ranked_sort(query, sort, supplier_profile_id)
        elif sort == "NAME_ASC":
            query = query.order_by(Product.name.asc())
        elif sort == "PRICE_ASC":
            query = query.order_by(Product.price_cents.asc())
        elif sort == "PRICE_DESC":
            query = query.order_by(Product.price_cents.desc())
        else:  # "NEWEST" and any unrecognised value both fall back to this
            query = query.order_by(Product.created_at.desc())

        offset = (page - 1) * limit
        products = query.offset(offset).limit(limit).all()
        return products, total_count

    @staticmethod
    def list_distinct_categories_for_supplier(supplier_profile_id: str | UUID) -> List[str]:
        """The real fix for a real bug: the category filter used to be
        derived from whatever products happened to be on the CURRENT
        PAGE, which broke the moment pagination existed (the list
        would shift depending on which page you were viewing). A
        supplier's own set of DISTINCT categories is small and bounded
        even when their product list is huge, so this is a cheap,
        direct query -- correct regardless of how many pages the
        catalogue has, and computed once, independent of whichever
        page/sort/filter the business currently has selected. Archived
        products excluded, same visibility rule as
        list_for_supplier_paginated above -- a business shouldn't see
        a filter option that only exists because of something the
        supplier pulled from sale."""
        rows = (
            db.session.query(Product.category)
            .filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False, is_archived=False)
            .distinct()
            .all()
        )
        return [row[0].value for row in rows]

    @staticmethod
    def list_related_products(
        supplier_profile_id: str | UUID, category: ProductCategory, exclude_product_id: str | UUID, limit: int = 5
    ) -> List[Product]:
        """"More from [Supplier]" -- genuinely related products FIRST
        (same category, same supplier, excluding the one currently
        being viewed), THEN backfilled with any OTHER product from
        this same supplier (any category) if fewer than `limit` were
        found -- confirmed during review: a supplier with real stock
        but few products in any one category would otherwise show
        NOTHING here far too often. Priority always goes to genuine
        relatedness -- backfill only ever fills the leftover slots,
        never displaces a real match. Still always excludes the
        current product and never duplicates a row that's already in
        the related set. Out-of-stock products are NOT excluded here
        -- same consistent behaviour as the main catalogue grid.
        Archived excluded throughout.

        RANKED, NOT JUST NEWEST. Both passes used to be plain
        created_at DESC, because when this was written there genuinely
        was no better signal available. There is now: the same-category
        pass uses RECOMMENDED (in stock -> deepest discount -> newest),
        and the backfill uses BEST_SELLING, so the products offered
        alongside the one you're looking at are ones that can actually
        be bought and that other businesses actually buy -- rather than
        whatever the supplier happened to upload most recently, which
        could easily be out of stock.

        The two passes use DIFFERENT rankings on purpose. Within a
        category, relevance is already established by the category
        itself, so what matters is "which of these should I buy" ->
        stock and price. Across categories there is no relevance at
        all, so popularity is the only honest ordering left."""
        related = (
            ProductRepository._apply_ranked_sort(
                Product.query.filter(
                    Product.supplier_profile_id == supplier_profile_id,
                    Product.category == category,
                    Product.id != exclude_product_id,
                    Product.is_deleted.is_(False),
                    Product.is_archived.is_(False),
                ),
                "RECOMMENDED",
                supplier_profile_id,
            )
            .limit(limit)
            .all()
        )

        remaining = limit - len(related)
        if remaining <= 0:
            return related

        already_included_ids = [exclude_product_id] + [p.id for p in related]
        backfill = (
            ProductRepository._apply_ranked_sort(
                Product.query.filter(
                    Product.supplier_profile_id == supplier_profile_id,
                    Product.id.notin_(already_included_ids),
                    Product.is_deleted.is_(False),
                    Product.is_archived.is_(False),
                ),
                # Popularity, not recency -- see this method's docstring
                # on why the two passes rank differently.
                "BEST_SELLING",
                supplier_profile_id,
            )
            .limit(remaining)
            .all()
        )
        return related + backfill

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
