"""
Supplier's own audit event vocabulary -- moved here from the single
flat AuditEventName enum, same reasoning as event_types/auth.py's own
docstring.

MEDIA_* VALUES ARE INCLUDED HERE DELIBERATELY, DESPITE THEIR "media."
STRING PREFIX -- every real publish() call for these passes
domain=AuditDomain.SUPPLIER (see products/jobs/deleted_product_media_sweep.py
and shared/media/jobs/orphan_upload_sweep.py), so they're genuinely
Supplier-domain events; the "media." prefix on the STRING VALUE itself
is a historical naming choice from before this file split existed, not
a signal they belong anywhere else. Changing the string values
themselves is out of scope for this refactor -- this is a pure code
reorganization, not a change to what's actually stored.
"""
from __future__ import annotations

import enum


class SupplierAuditEvent(str, enum.Enum):
    PRODUCT_CREATE_RATE_LIMITED = "supplier.product_create_rate_limited"
    PRODUCT_BULK_ACTION_RATE_LIMITED = "supplier.product_bulk_action_rate_limited"
    INVENTORY_ADJUST_RATE_LIMITED = "supplier.inventory_adjust_rate_limited"
    MEDIA_SIGN_RATE_LIMITED = "supplier.media_sign_rate_limited"
    PRODUCT_MEDIA_REJECTED = "supplier.product_media_rejected"
    SUPPLIER_PROFILE_IMAGE_REJECTED = "supplier.profile_image_rejected"
    BULK_IMPORT_SUBMIT_RATE_LIMITED = "supplier.bulk_import_submit_rate_limited"
    BULK_IMPORT_SUSPICIOUS_FILE_DETECTED = "supplier.bulk_import_suspicious_file_detected"
    BULK_IMPORT_LOCKED_OUT = "supplier.bulk_import_locked_out"
    MEDIA_ORPHAN_ASSET_CLEANED = "media.orphan_asset_cleaned"
    MEDIA_DELETED_PRODUCT_ASSET_CLEANED = "media.deleted_product_asset_cleaned"
    ORDER_APPROVED = "supplier.order_approved"
    ORDER_DECLINED = "supplier.order_declined"
    ORDER_AUTO_DECLINED = "supplier.order_auto_declined"
    ORDER_CANCELLED = "supplier.order_cancelled"

    #: A supplier's plan was changed by staff.
    #:
    #: AUDITED BECAUSE IT IS A COMMERCIAL ACT, not a configuration
    #: tweak. A plan decides how much reach somebody gets and, for
    #: PARTNER, was negotiated by a person -- so "who put this supplier
    #: on MAX, when, and on what basis" is a question that WILL be
    #: asked, most likely by the supplier who is being billed or by the
    #: one who thinks a competitor got something they did not.
    PLAN_CHANGED = "supplier.plan_changed"
