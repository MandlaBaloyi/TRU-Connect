"""
Centralized Cloudinary folder-naming convention. ONE place every
domain's own upload path calls into -- confirmed during review: the
taxonomy is organized by WHO an asset belongs to (a supplier, a
business, the platform itself), not by WHAT TYPE it is, so an admin
reviewing one supplier's verification documents can browse that
supplier's whole folder rather than hunting across a type-first
structure.

TWO SEPARATE THINGS, NOT ONE -- every function here returns a path
used for BOTH public_id (permanent, baked into the asset's real URL,
never changes) AND asset_folder (purely how Cloudinary's Media Library
UI organizes things for browsing). These look identical today, but
they're independent concepts to Cloudinary itself: a real, confirmed
gap found during review was setting public_id's path correctly while
never setting asset_folder at all, which on a Dynamic-Folder-Mode
account (the default for any Cloudinary account created after
June 2024) means NOTHING ever shows up in the browsable Folders tree,
even though every asset is still find-able by search. See
providers/cloudinary_provider.py's own docstring for exactly where
both get set.

FULL TAXONOMY -- three account types this platform actually has
(supplier, business/"informal business", and the platform/admin side
itself), each gets its own top-level branch:

    tru_connect/suppliers/{supplier_profile_id}/products/{product_id}/{asset_id}   [BUILT, ACTIVE]
    tru_connect/suppliers/{supplier_profile_id}/profile/{asset_id}                  [reserved]
    tru_connect/suppliers/{supplier_profile_id}/documents/{asset_id}                [reserved]

    tru_connect/businesses/{business_id}/profile/{asset_id}                        [reserved]
    tru_connect/businesses/{business_id}/documents/{asset_id}                      [reserved]
    tru_connect/businesses/{business_id}/proof-of-payment/{order_id}/{asset_id}    [reserved]

    tru_connect/admin/platform/{asset_id}                                          [reserved]

"Reserved" branches are documented here so the FIRST real caller for
each matches this convention exactly rather than improvising a new
one -- admin itself never uploads a supplier's or business's own
documents; it only ever REVIEWS what already lives under their own
branches above, which is why there's no separate "admin reviews X"
path -- review is a permission/role concern (who's allowed to look),
not a storage-location concern (where the file actually lives).
tru_connect/admin/platform/ is reserved for the one thing admin WOULD
genuinely own itself later -- platform-level assets like banners or
announcements, not owned by any one supplier or business.

REAL DATABASE IDs ARE NEVER USED DIRECTLY IN A CLOUDINARY PATH -- found
during a security review: a real supplier_profile_id or product_id
sitting directly in a third-party vendor's own folder tree is an
unnecessary information exposure, even though it isn't independently
exploitable on its own (ownership is always enforced by a signed JWT
plus a real database check on every request -- knowing an ID alone
never grants access to anything). _obscure() derives a different,
deterministic string via HMAC-SHA256 keyed on this app's own
SECRET_KEY: the SAME real ID always produces the SAME obscured value
(so every existing lookup/ownership-check call site keeps working
completely unchanged, since building a path and verifying one both
route through this same function), but the real ID can't be recovered
from it without knowing that secret. Read directly via os.environ
rather than Flask's current_app.config -- this module needs to work
identically whether called from a request or a background sweep job,
same reasoning as MediaConfig's own docstring.
"""
from __future__ import annotations

import hashlib
import hmac
import os

ROOT = "tru_connect"


def _obscure(real_id) -> str:
    secret = os.environ.get("SECRET_KEY", "").encode("utf-8")
    return hmac.new(secret, str(real_id).encode("utf-8"), hashlib.sha256).hexdigest()


def supplier_product_folder(supplier_profile_id, product_id) -> str:
    obscured_supplier = _obscure(supplier_profile_id)
    obscured_product = _obscure(product_id)
    return f"{ROOT}/suppliers/{obscured_supplier}/products/{obscured_product}"


def is_supplier_product_asset(public_id: str) -> bool:
    """Webhook dispatch can no longer use a simple prefix match --
    supplier_profile_id sits BEFORE the "products" segment in the new
    who-owns-it-first taxonomy, so there's no fixed string every
    product asset starts with. Matched by segment instead: distinctive
    enough ("/products/" won't appear in a future "/documents/" or
    "/profile/" path) without needing to know or care about the
    variable supplier_profile_id in between."""
    return "/products/" in public_id
