"""
Centralized Cloudinary folder-naming convention. ONE place every
domain's own upload path calls into -- confirmed during review: the
taxonomy is organized by WHO an asset belongs to (a supplier, a
business), not by WHAT TYPE it is, so an admin reviewing one
supplier's verification documents can browse that supplier's whole
folder rather than hunting across a type-first structure.

Current shape:
    tru_connect/suppliers/{supplier_profile_id}/products/{product_id}/{asset_id}

Reserved, not yet used (documented here so the FIRST real caller for
each matches this convention exactly rather than improvising a new
one):
    tru_connect/suppliers/{supplier_profile_id}/profile/{asset_id}
    tru_connect/suppliers/{supplier_profile_id}/documents/{asset_id}
    tru_connect/businesses/{business_id}/profile/{asset_id}
    tru_connect/businesses/{business_id}/documents/{asset_id}
    tru_connect/businesses/{business_id}/proof-of-payment/{order_id}/{asset_id}
"""
from __future__ import annotations

ROOT = "tru_connect"


def supplier_product_folder(supplier_profile_id, product_id) -> str:
    return f"{ROOT}/suppliers/{supplier_profile_id}/products/{product_id}"


def is_supplier_product_asset(public_id: str) -> bool:
    """Webhook dispatch can no longer use a simple prefix match --
    supplier_profile_id sits BEFORE the "products" segment in the new
    who-owns-it-first taxonomy, so there's no fixed string every
    product asset starts with. Matched by segment instead: distinctive
    enough ("/products/" won't appear in a future "/documents/" or
    "/profile/" path) without needing to know or care about the
    variable supplier_profile_id in between."""
    return "/products/" in public_id
