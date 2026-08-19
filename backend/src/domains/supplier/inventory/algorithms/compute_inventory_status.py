"""
compute_inventory_status / compute_available_quantity -- mirrors
frontend/src/features/dashboard/supplier/inventory/algorithms/
computeInventoryStatus.ts exactly, including the order-of-checks
reasoning: zero-or-below is OUT_OF_STOCK even if the threshold is also
0 (a threshold of 0 doesn't mean "never low stock"). The core rule
Inventory exists to enforce -- the supplier manages quantity, TRU
Connect manages status -- lives in exactly one place per side (this
file on the backend, that file on the frontend); neither is a
duplicate of the other's logic, they're the same rule implemented
twice because the frontend needs an immediate preview and the backend
needs to be the actual source of truth.
"""
from __future__ import annotations


def compute_available_quantity(quantity_on_hand: int, quantity_reserved: int) -> int:
    return max(0, quantity_on_hand - quantity_reserved)


def compute_inventory_status(quantity_on_hand: int, low_stock_threshold: int) -> str:
    if quantity_on_hand <= 0:
        return "OUT_OF_STOCK"
    if quantity_on_hand <= low_stock_threshold:
        return "LOW_STOCK"
    return "IN_STOCK"
