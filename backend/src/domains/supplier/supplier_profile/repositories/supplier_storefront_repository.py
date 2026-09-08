"""
SupplierStorefrontSection repository -- ONLY talks to SQLAlchemy, no
business rules, same discipline as every other repository here.
"""
from __future__ import annotations

from typing import List
from uuid import UUID

from src.extensions import db
from src.domains.supplier.products.models.product import Product
from src.domains.supplier.supplier_profile.models.supplier_storefront import (
    SupplierStorefrontSection,
    SupplierStorefrontSectionProduct,
)


class SupplierStorefrontRepository:
    @staticmethod
    def list_enabled_for_supplier(supplier_profile_id: str | UUID) -> List[SupplierStorefrontSection]:
        """The sections this supplier is actually running, in their own
        order.

        Returns an EMPTY LIST for a supplier who has configured
        nothing, which the service treats as "use the defaults" rather
        than "show no storefront" -- see its own docstring on why no
        rows are created on read.
        """
        return (
            SupplierStorefrontSection.query.filter(
                SupplierStorefrontSection.supplier_profile_id == supplier_profile_id,
                SupplierStorefrontSection.is_enabled.is_(True),
                SupplierStorefrontSection.is_deleted.is_(False),
            )
            .order_by(SupplierStorefrontSection.position.asc(), SupplierStorefrontSection.created_at.asc())
            .all()
        )

    @staticmethod
    def list_all_for_supplier(supplier_profile_id: str | UUID) -> List[SupplierStorefrontSection]:
        """Enabled AND disabled -- what the SUPPLIER'S own settings
        screen needs, where a switched-off section still has to appear
        so it can be switched back on."""
        return (
            SupplierStorefrontSection.query.filter(
                SupplierStorefrontSection.supplier_profile_id == supplier_profile_id,
                SupplierStorefrontSection.is_deleted.is_(False),
            )
            .order_by(SupplierStorefrontSection.position.asc(), SupplierStorefrontSection.created_at.asc())
            .all()
        )

    @staticmethod
    def list_products_for_section(section_id: str | UUID) -> List[Product]:
        """The supplier's chosen products, in the order they chose.

        JOINS THROUGH TO Product AND FILTERS THERE, rather than
        returning the join rows: a product the supplier archived or
        deleted after adding it to a strip must vanish from that strip
        immediately, without anyone having to remember to clean the
        join table up. The stale row stays -- harmless, and it means
        un-archiving a product silently restores it to the strip it was
        always in.
        """
        return (
            db.session.query(Product)
            .join(
                SupplierStorefrontSectionProduct,
                SupplierStorefrontSectionProduct.product_id == Product.id,
            )
            .filter(
                SupplierStorefrontSectionProduct.section_id == section_id,
                SupplierStorefrontSectionProduct.is_deleted.is_(False),
                Product.is_deleted.is_(False),
                Product.is_archived.is_(False),
            )
            .order_by(SupplierStorefrontSectionProduct.position.asc())
            .all()
        )
