"""
Inventory Service -- composes Products (fetched via the products
domain's own repository, never duplicated) with Inventory records,
computing status/available quantity fresh on every read. Business
rules live here; InventoryRepository/InventorySettingsRepository stay
pure SQL, same split as every other domain.

CROSS-DOMAIN READ, NOT A CIRCULAR IMPORT -- this service reads
SupplierOfferRepository directly (inventory depends on products), but
products/services/product_service.py never imports anything from
here. That's a one-directional dependency, the same shape
connections' catalog_service already has on products (reads it for the
ordering gate), not a cycle -- confirmed during the media-architecture
planning discussion as the deliberate reason product_media ended up
living inside products/ rather than shared/media owning a table:
avoiding exactly this kind of two-way dependency between domains'
data layers.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.inventory.algorithms.compute_inventory_status import (
    compute_available_quantity,
    compute_inventory_status,
)
from src.domains.supplier.inventory.models.inventory import Inventory, LowStockAlertChannel
from src.domains.supplier.inventory.repositories.inventory_repository import (
    InventoryRepository,
    InventorySettingsRepository,
)
from src.domains.supplier.inventory.services.errors import InsufficientStockError, InventoryValidationError
from src.domains.supplier.inventory.services.errors import ProductNotFoundError as InventoryProductNotFoundError
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository


def _compose(product, inventory: Inventory) -> dict:
    status = compute_inventory_status(inventory.quantity_on_hand, inventory.low_stock_threshold)
    available = compute_available_quantity(inventory.quantity_on_hand, inventory.quantity_reserved)
    return {"product": product, "inventory": inventory, "status": status, "available_quantity": available}


def get_inventory_list(
    supplier_profile_id: str | UUID, status_filter: Optional[str] = None, search_term: Optional[str] = None
) -> List[dict]:
    products = SupplierOfferRepository.list_for_supplier(supplier_profile_id, search_term=search_term)
    items = [
        _compose(product, InventoryRepository.get_or_create_for_product(product.id, supplier_profile_id))
        for product in products
    ]
    if status_filter and status_filter != "ALL":
        items = [item for item in items if item["status"] == status_filter]
    return items


def get_inventory_item(product_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise InventoryProductNotFoundError("Product not found.")
    inventory = InventoryRepository.get_or_create_for_product(product_id, supplier_profile_id)
    return _compose(product, inventory)


def get_inventory_summary(supplier_profile_id: str | UUID) -> dict:
    items = get_inventory_list(supplier_profile_id)
    return {
        "total_products": len(items),
        "in_stock_count": sum(1 for i in items if i["status"] == "IN_STOCK"),
        "low_stock_count": sum(1 for i in items if i["status"] == "LOW_STOCK"),
        "out_of_stock_count": sum(1 for i in items if i["status"] == "OUT_OF_STOCK"),
    }


def adjust_stock(
    product_id: str | UUID,
    supplier_profile_id: str | UUID,
    quantity_delta: int,
    reason: str,
    commit: bool = True,
) -> dict:
    """commit=False: bulk callers only (import seeds stock per row).
    See SupplierOfferRepository.create for why."""
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise InventoryProductNotFoundError("Product not found.")

    inventory = InventoryRepository.get_or_create_for_product(
        product_id, supplier_profile_id, commit=commit
    )
    next_on_hand = inventory.quantity_on_hand + quantity_delta
    if next_on_hand < 0:
        raise InsufficientStockError(
            f"That would take stock below zero (currently {inventory.quantity_on_hand})."
        )

    # reason is accepted and validated (schema) but not yet persisted
    # anywhere -- inventory_movements (the audit trail of every
    # adjustment) is a deliberate follow-up, not built this phase, per
    # the design notes' own "don't build this before Products ->
    # Inventory -> Orders works" sequencing. Accepting it now means the
    # contract this endpoint commits to never has to change when that
    # table lands -- only this function's body does.
    del reason

    updated = InventoryRepository.adjust_quantity(inventory, quantity_delta, commit=commit)
    return _compose(product, updated)


def set_low_stock_threshold(product_id: str | UUID, supplier_profile_id: str | UUID, threshold: int) -> dict:
    product = SupplierOfferRepository.get_by_id_and_supplier(product_id, supplier_profile_id)
    if not product:
        raise InventoryProductNotFoundError("Product not found.")
    if threshold < 0:
        raise InventoryValidationError(
            "Low-stock threshold can't be negative.", errors=["Low-stock threshold can't be negative."]
        )

    inventory = InventoryRepository.get_or_create_for_product(product_id, supplier_profile_id)
    updated = InventoryRepository.set_threshold(inventory, threshold)
    return _compose(product, updated)


def get_settings(supplier_profile_id: str | UUID):
    return InventorySettingsRepository.get_or_create_for_supplier(supplier_profile_id)


def update_settings(
    supplier_profile_id: str | UUID,
    default_low_stock_threshold: Optional[int] = None,
    low_stock_alert_channel: Optional[str] = None,
):
    if default_low_stock_threshold is not None and default_low_stock_threshold < 0:
        raise InventoryValidationError(
            "Default low-stock threshold can't be negative.", errors=["Default low-stock threshold can't be negative."]
        )

    settings = InventorySettingsRepository.get_or_create_for_supplier(supplier_profile_id)
    channel = LowStockAlertChannel(low_stock_alert_channel) if low_stock_alert_channel else None
    return InventorySettingsRepository.update(
        settings,
        default_low_stock_threshold=default_low_stock_threshold,
        low_stock_alert_channel=channel,
    )
