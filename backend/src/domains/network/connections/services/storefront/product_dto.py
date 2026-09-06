"""
The one enriched product shape every business-facing storefront read
returns. Shared by the catalogue list, related products and the profile
showcase -- they all need the identical fields, and duplicating this
risks them silently drifting apart.
"""
from __future__ import annotations

from typing import List

def build_catalog_product_dicts(products: List) -> List[dict]:
    """Shared by list_supplier_products, list_related_products and
    list_profile_products -- all need the exact same enriched shape
    (compareAtPriceCents, inStock, approved-only images), and
    duplicating this risks them silently drifting apart over time.
    Batches the inventory lookup, not one query per product -- same
    "protect the API" discipline as pagination itself. A product with
    no matching inventory row is treated as zero available (the same
    default value a real row would have anyway), never created as a
    side effect of this read -- see InventoryRepository.
    list_by_product_ids' own docstring on why a business simply
    browsing must never trigger a write to the supplier's own
    inventory rows."""
    from src.domains.supplier.inventory.repositories.inventory_repository import InventoryRepository
    from src.domains.supplier.products.services import product_media_service

    inventory_rows = InventoryRepository.list_by_product_ids([p.id for p in products])
    available_by_product = {row.product_id: row.quantity_on_hand - row.quantity_reserved for row in inventory_rows}

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category.value,
            "priceCents": p.price_cents,
            # Added so a business browsing this catalogue can see the
            # same "was RX, now RY" / "% OFF" badge the supplier
            # themselves sees on their own product screens -- the
            # underlying discount is real regardless of who's looking
            # at it.
            "compareAtPriceCents": p.compare_at_price_cents,
            "sellingUnit": p.selling_unit.value,
            # A real, direct answer to "can I actually order this
            # right now" -- never the exact quantity (a business
            # doesn't need to know "exactly 3 left", only whether
            # it's currently orderable at all; the supplier's own
            # exact count stays theirs).
            "inStock": available_by_product.get(p.id, 0) > 0,
            # Real, APPROVED-only media -- this is exactly the endpoint
            # a business actually sees, so it's the one place this
            # matters most (see product_media_service's own
            # list_approved_media docstring for why only APPROVED ever
            # reaches here).
            "images": product_media_service.list_approved_media(p.id),
        }
        for p in products
    ]
