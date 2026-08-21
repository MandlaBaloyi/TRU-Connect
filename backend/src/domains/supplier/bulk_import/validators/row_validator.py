"""
validate_row -- mirrors frontend/src/features/dashboard/supplier/
bulk-products/services/rowValidator.ts field-for-field, including
error message wording, on purpose: the client-side preview and this
server-side re-validation must agree, or a supplier who saw "2,493
valid rows" in the preview and then gets a different count back from
the real import would rightly distrust the whole feature. This is the
SERVER'S OWN copy of that logic, not a shared library -- Python and
TypeScript can't share code directly, so the discipline is keeping the
two hand-in-sync deliberately, the same way computeInventoryStatus
exists once per side for the identical reason.

Collects EVERY field error on a row, not just the first -- matches the
frontend's own reasoning exactly (a supplier fixing errors one pass at
a time for a 2,000-row file would be miserable).
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.domains.supplier.products.models.product import ProductCategory, ProductUnit

IMAGE_COLUMN_HEADERS = ["image_1", "image_2", "image_3", "image_4", "image_5"]

_CATEGORY_BY_CODE = {c.value.lower(): c for c in ProductCategory}
_UNIT_BY_CODE = {u.value.lower(): u for u in ProductUnit}

# Human-readable labels, matching the frontend's own CATEGORY_OPTIONS/
# UNIT_OPTIONS exactly -- a supplier's spreadsheet contains "Beverages"
# and "Bottle", never "BEVERAGES"/"BOTTLE". Kept as an explicit map
# here (not derived from the enum) since the enum's own values ARE the
# machine codes, and the label wording ("Snacks & Confectionery") isn't
# mechanically derivable from SNACKS_CONFECTIONERY.
_CATEGORY_LABELS: Dict[ProductCategory, str] = {
    ProductCategory.FOOD_GROCERY: "Food & Grocery",
    ProductCategory.BEVERAGES: "Beverages",
    ProductCategory.SNACKS_CONFECTIONERY: "Snacks & Confectionery",
    ProductCategory.BAKERY: "Bakery",
    ProductCategory.DAIRY_CHILLED: "Dairy & Chilled",
    ProductCategory.FRESH_PRODUCE: "Fresh Produce",
    ProductCategory.MEAT_FROZEN: "Meat & Frozen",
    ProductCategory.HOUSEHOLD_CLEANING: "Household & Cleaning",
    ProductCategory.PERSONAL_CARE: "Personal Care",
    ProductCategory.BABY_FAMILY: "Baby & Family",
    ProductCategory.STATIONERY_SCHOOL: "Stationery & School",
    ProductCategory.HARDWARE_GENERAL: "Hardware & General",
    ProductCategory.ELECTRONICS_ACCESSORIES: "Electronics & Accessories",
    ProductCategory.PACKAGING_DISPOSABLE: "Packaging & Disposable",
    ProductCategory.CLOTHING_APPAREL: "Clothing & Apparel",
    ProductCategory.OTHER: "Other",
}
_UNIT_LABELS: Dict[ProductUnit, str] = {
    ProductUnit.EACH: "Each",
    ProductUnit.PACK: "Pack",
    ProductUnit.BOX: "Box",
    ProductUnit.CASE: "Case",
    ProductUnit.BAG: "Bag",
    ProductUnit.BOTTLE: "Bottle",
    ProductUnit.CAN: "Can",
    ProductUnit.DOZEN: "Dozen",
    ProductUnit.KG: "kg",
    ProductUnit.G: "g",
    ProductUnit.L: "L",
    ProductUnit.ML: "ml",
}
_CATEGORY_LABEL_LOOKUP = {v.lower(): k for k, v in _CATEGORY_LABELS.items()}
_UNIT_LABEL_LOOKUP = {v.lower(): k for k, v in _UNIT_LABELS.items()}


def _suggest_closest(raw: str, valid_labels: List[str]) -> Optional[str]:
    """"Did you mean X?" for a genuinely unrecognised value -- NEVER
    auto-applied, only offered. Unlike a case difference (always safe
    to resolve automatically, see zip cross-reference in
    import_worker.py), a typo in a category or unit name is genuinely
    ambiguous -- guessing wrong here would silently file a product
    under the wrong category, which is worse than an honest error the
    supplier has to actually look at and confirm."""
    matches = difflib.get_close_matches(raw.strip(), valid_labels, n=1, cutoff=0.6)
    return matches[0] if matches else None


def match_category(raw: str) -> Optional[ProductCategory]:
    q = raw.strip().lower()
    if not q:
        return None
    return _CATEGORY_LABEL_LOOKUP.get(q) or _CATEGORY_BY_CODE.get(q)


def match_unit(raw: str) -> Optional[ProductUnit]:
    q = raw.strip().lower()
    if not q:
        return None
    return _UNIT_LABEL_LOOKUP.get(q) or _UNIT_BY_CODE.get(q)


def parse_cents_input(raw: str) -> Optional[int]:
    """Mirrors productMapper.ts's own parseCentsInput exactly: strips
    an optional "R" prefix, treats a comma as a decimal point, requires
    1-2 decimal digits if present."""
    cleaned = re.sub(r"^R\s*", "", raw.strip(), flags=re.IGNORECASE).replace(",", ".")
    if cleaned == "":
        return None
    if not re.match(r"^\d+(\.\d{1,2})?$", cleaned):
        return None
    rands = float(cleaned)
    if rands < 0:
        return None
    return round(rands * 100)


def parse_quantity(raw: str) -> Tuple[Optional[int], Optional[str]]:
    trimmed = raw.strip()
    if not trimmed:
        return 0, None
    if not re.match(r"^\d+$", trimmed):
        return None, f'Invalid quantity: "{raw}". Use a whole number, e.g. 50.'
    return int(trimmed), None


@dataclass
class RowError:
    field: str
    message: str


@dataclass
class ImageReference:
    column: str
    filename: str


@dataclass
class ParsedRow:
    row_number: int
    raw: Dict[str, str]
    name: Optional[str]
    category: Optional[ProductCategory]
    price_cents: Optional[int]
    selling_unit: Optional[ProductUnit]
    quantity: Optional[int]
    image_references: List[ImageReference] = field(default_factory=list)
    errors: List[RowError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def validate_row(raw: Dict[str, str], row_number: int) -> ParsedRow:
    errors: List[RowError] = []

    name_raw = raw.get("name", "")
    name = name_raw.strip() or None
    if not name:
        errors.append(RowError("name", "Product name is required."))

    category = match_category(raw.get("category", ""))
    if not category:
        raw_category = raw.get("category", "")
        if raw_category:
            message = f'Category not recognised: "{raw_category}".'
            suggestion = _suggest_closest(raw_category, list(_CATEGORY_LABELS.values()))
            if suggestion:
                message += f' Did you mean "{suggestion}"?'
        else:
            message = "Category is required."
        errors.append(RowError("category", message))

    price_cents = parse_cents_input(raw.get("price", ""))
    if price_cents is None:
        raw_price = raw.get("price", "")
        message = f'Invalid price: "{raw_price}".' if raw_price else "Price is required."
        errors.append(RowError("price", message))

    selling_unit = match_unit(raw.get("unit", ""))
    if not selling_unit:
        raw_unit = raw.get("unit", "")
        if raw_unit:
            message = f'Unit not recognised: "{raw_unit}".'
            suggestion = _suggest_closest(raw_unit, list(_UNIT_LABELS.values()))
            if suggestion:
                message += f' Did you mean "{suggestion}"?'
        else:
            message = "Unit is required."
        errors.append(RowError("unit", message))

    quantity, quantity_error = parse_quantity(raw.get("quantity", ""))
    if quantity_error:
        errors.append(RowError("quantity", quantity_error))

    image_references = [
        ImageReference(column=col, filename=raw.get(col, "").strip())
        for col in IMAGE_COLUMN_HEADERS
        if raw.get(col, "").strip()
    ]

    return ParsedRow(
        row_number=row_number,
        raw=raw,
        name=name,
        category=category,
        price_cents=price_cents,
        selling_unit=selling_unit,
        quantity=quantity,
        image_references=image_references,
        errors=errors,
    )
