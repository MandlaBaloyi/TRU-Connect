"""
Generates the supplier's own default tracking label -- SKU-000001,
SKU-000002, one counter PER SUPPLIER (not platform-wide, matching how
SKUs actually work in the real world: every business has its own
numbering), always moving forward, never reused even if a product is
later deleted or its SKU overridden. Only ever called when a supplier
leaves the SKU field blank, so every product still ends up with a
stable, reportable label to group sales/profit/order-count by.

6 DIGITS -- gives real headroom for a genuinely large catalogue
(999,999 products for one supplier) before ever needing a wider
format. Existing SKU-0001-style values already issued before this
change stay valid forever -- sku is a plain string column, nothing
parses or re-derives a number from it, so a shorter, already-issued
value causes no functional problem; only NEW SKUs from this point
forward use the wider padding.

NOT derived by counting or parsing existing SKU text -- a supplier who
types their own custom SKU ("BREAD-CASE-24") must never influence what
number this generator produces next. The counter lives on its own
dedicated column, SupplierProfile.next_sku_sequence, which nothing
else touches.

ATOMIC BY CONSTRUCTION -- uses a single UPDATE ... RETURNING to read
and increment the counter in one indivisible database operation, so
two products created for the same supplier at the same moment can
never receive the same number.
"""
from __future__ import annotations

from src.domains.supplier.supplier_profile.models.supplier_profile import SupplierProfile
from src.extensions import db


def generate_sku(supplier_profile_id) -> str:
    result = db.session.execute(
        db.update(SupplierProfile)
        .where(SupplierProfile.id == supplier_profile_id)
        .values(next_sku_sequence=SupplierProfile.next_sku_sequence + 1)
        .returning(SupplierProfile.next_sku_sequence)
    )
    new_counter_value = result.scalar_one()
    db.session.commit()

    # new_counter_value is what the counter became AFTER incrementing
    # -- subtract 1 to get the number THIS product actually gets, so
    # the very first product issued is SKU-000001, not SKU-000002.
    issued_value = new_counter_value - 1
    return f"SKU-{issued_value:06d}"
