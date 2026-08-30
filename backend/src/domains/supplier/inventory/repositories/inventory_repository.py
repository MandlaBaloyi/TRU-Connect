"""
Inventory + InventorySettings repositories -- ONLY talk to SQLAlchemy,
no business rules, same rule as every other repository in this
codebase.

get_or_create_for_product LAZILY creates an inventory row the first
time anything looks a product up -- mirrors the frontend mock's own
getOrCreateInventoryItem exactly (same reasoning: a product created
before Inventory existed, or created without an initial quantity, has
no row yet; a real backend would ideally seed this via a DB
default/trigger at product-creation time, but a lazy read-time check
achieves the identical contract without coupling product_service.py
to this domain at all -- Products still doesn't need to know Inventory
exists).
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from src.domains.supplier.inventory.models.inventory import Inventory, InventorySettings, LowStockAlertChannel
from src.extensions import db

DEFAULT_LOW_STOCK_THRESHOLD = 5


class InventorySettingsRepository:
    @staticmethod
    def get_or_create_for_supplier(supplier_profile_id: str | UUID) -> InventorySettings:
        settings = InventorySettings.query.filter_by(
            supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()
        if settings is None:
            settings = InventorySettings(
                supplier_profile_id=supplier_profile_id,
                default_low_stock_threshold=DEFAULT_LOW_STOCK_THRESHOLD,
                low_stock_alert_channel=LowStockAlertChannel.IN_APP,
            )
            db.session.add(settings)
            db.session.commit()
        return settings

    @staticmethod
    def update(settings: InventorySettings, **fields) -> InventorySettings:
        for key, value in fields.items():
            if value is not None:
                setattr(settings, key, value)
        db.session.commit()
        return settings


class InventoryRepository:
    @staticmethod
    def get_by_product_id(product_id: str | UUID) -> Optional[Inventory]:
        return Inventory.query.filter_by(product_id=product_id, is_deleted=False).first()

    @staticmethod
    def get_by_product_and_supplier(product_id: str | UUID, supplier_profile_id: str | UUID) -> Optional[Inventory]:
        return Inventory.query.filter_by(
            product_id=product_id, supplier_profile_id=supplier_profile_id, is_deleted=False
        ).first()

    @staticmethod
    def get_or_create_for_product(product_id: str | UUID, supplier_profile_id: str | UUID) -> Inventory:
        inventory = InventoryRepository.get_by_product_id(product_id)
        if inventory is not None:
            return inventory

        settings = InventorySettingsRepository.get_or_create_for_supplier(supplier_profile_id)
        inventory = Inventory(
            product_id=product_id,
            supplier_profile_id=supplier_profile_id,
            quantity_on_hand=0,
            quantity_reserved=0,
            low_stock_threshold=settings.default_low_stock_threshold,
        )
        db.session.add(inventory)
        db.session.commit()
        return inventory

    @staticmethod
    def list_for_supplier(supplier_profile_id: str | UUID) -> List[Inventory]:
        return Inventory.query.filter_by(supplier_profile_id=supplier_profile_id, is_deleted=False).all()

    @staticmethod
    def list_by_product_ids(product_ids: List[str | UUID]) -> List[Inventory]:
        """READ-ONLY, deliberately NOT get_or_create_for_product -- this
        exists for the business-facing catalogue view (connections_
        service.py's own list_supplier_products/get_supplier_product),
        where a business simply BROWSING a supplier's catalogue must
        never trigger a write to that supplier's own inventory rows.
        A product with no matching row here just means "no inventory
        row exists yet" -- treated as zero available at the SERVICE
        layer (same default value a real row would have anyway), never
        created as a side effect of a read."""
        if not product_ids:
            return []
        return Inventory.query.filter(Inventory.product_id.in_(product_ids), Inventory.is_deleted.is_(False)).all()

    @staticmethod
    def adjust_quantity(inventory: Inventory, quantity_delta: int) -> Inventory:
        inventory.quantity_on_hand = inventory.quantity_on_hand + quantity_delta
        db.session.commit()
        return inventory

    @staticmethod
    def set_threshold(inventory: Inventory, low_stock_threshold: int) -> Inventory:
        inventory.low_stock_threshold = low_stock_threshold
        db.session.commit()
        return inventory
