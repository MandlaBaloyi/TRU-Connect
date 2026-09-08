"""
pinned_products_service -- the supplier's "feature these on my business
profile" curation.

WRITES (pin/unpin) are supplier-facing, reached from the Products
screen's per-card ⋮ menu (products_routes.py). The business-facing
brand profile reads list_pinned_product_ids to float pinned products to
the front of their category's showcase strip
(connections' catalog_service._group_profile_showcase).
"""
from __future__ import annotations

from typing import Set
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.supplier_profile.repositories.supplier_pinned_product_repository import (
    SupplierPinnedProductRepository,
)
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError

MAX_PINNED = 6


def pin(supplier_profile_id: str | UUID, product_id: str | UUID) -> None:
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if product is None:
        raise NotFoundError("Product not found.", code="PRODUCT_NOT_FOUND")
    if product.is_archived:
        raise ProfileValidationError(
            "You can't feature an archived product.",
            errors=["Unarchive the product first, then feature it."],
        )

    if SupplierPinnedProductRepository.get(supplier_profile_id, product_id) is not None:
        return  # idempotent -- already featured

    if SupplierPinnedProductRepository.count(supplier_profile_id) >= MAX_PINNED:
        raise ProfileValidationError(
            f"You can feature up to {MAX_PINNED} products on your profile.",
            errors=[f"Remove one before adding another (max {MAX_PINNED})."],
        )

    next_order = SupplierPinnedProductRepository.max_pin_order(supplier_profile_id) + 1
    SupplierPinnedProductRepository.add(supplier_profile_id, product_id, next_order)


def unpin(supplier_profile_id: str | UUID, product_id: str | UUID) -> None:
    pin_row = SupplierPinnedProductRepository.get(supplier_profile_id, product_id)
    if pin_row is not None:
        SupplierPinnedProductRepository.remove(pin_row)


def list_pinned_product_ids(supplier_profile_id: str | UUID) -> Set[UUID]:
    """For products_routes._to_dto's own `is_pinned` flag -- one query,
    then a membership check per product."""
    return SupplierPinnedProductRepository.list_product_ids(supplier_profile_id)


def is_pinned(supplier_profile_id: str | UUID, product_id: str | UUID) -> bool:
    return SupplierPinnedProductRepository.get(supplier_profile_id, product_id) is not None
