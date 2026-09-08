"""
THE CANONICAL IMPORT FIELD SET -- what a supplier can tell us about a
product, defined exactly once.

WHY THIS FILE EXISTS. A supplier's catalogue reaches TRU Connect through
more than one door: a CSV or XLSX upload today, a push from their own
system later. Those are the same FIELDS arriving in different
containers, and the moment the list is written out twice -- once as
column headers, once as JSON keys -- they drift.

That is not a hypothetical. This codebase has now hit "the same rule
written out N times" twice in a row, in consecutive steps:

  the connection gate lived in ordering_gate AND checkout_service, and
  flipping one would have left the app saying "you can order" and then
  refusing at checkout

  the direct payment rail was listed in five places, and DIRECT was
  added to two of them -- so the platform's own payment method could not
  complete a checkout at all

Both were caught late and neither was hard to prevent. The API adapter
has not been written yet, so this is the last cheap moment to make one
definition instead of two.

WHAT DERIVES FROM IT: the CSV parser's required and known column lists,
the downloadable template, and the request schema for the future API
push. Adding a field means adding one entry here.

NEW FIELDS ARE OPTIONAL, ALWAYS. Every supplier who already has a
template must keep working -- a required column added today breaks
files that were valid yesterday, for no gain the supplier asked for.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ImportField:
    """One thing a supplier can tell us, in whatever container it
    arrives."""

    #: The CSV column header, lowercased -- and the JSON key when the
    #: API adapter arrives. Deliberately the same string for both, so
    #: a supplier moving from file upload to integration does not have
    #: to relearn their own field names.
    name: str
    required: bool
    #: Shown in the downloadable template and any mapping UI. Written
    #: for a supplier, not for an engineer.
    help_text: str


#: The five image columns, kept as their own group because they are
#: positional rather than named -- image_1 through image_5 -- and the
#: zip cross-reference walks them as a set.
IMAGE_FIELD_NAMES: Tuple[str, ...] = ("image_1", "image_2", "image_3", "image_4", "image_5")


IMPORT_FIELDS: Tuple[ImportField, ...] = (
    ImportField("name", True, "What the product is called."),
    ImportField("category", True, "One of the TRU Connect categories, e.g. Beverages."),
    ImportField("price", True, "What a business pays, in rands."),
    ImportField("unit", True, "How you sell it: Each, Case, Box, Bag..."),
    ImportField("quantity", False, "How many you have in stock right now."),
    ImportField("sku", False, "Your own product code. Include it and a re-uploaded price file UPDATES these products instead of adding duplicates."),
    ImportField("description", False, "Anything a business should know before ordering."),
    ImportField("compare_at_price", False, "The old price, if this is on sale. Must be higher than the price."),
    # --- v2 step 6: the fields that make matching work ------------------
    ImportField("barcode", False, "The barcode on the item. The single most useful column you can fill in -- a barcode matches your product to our catalogue instantly and exactly."),
    ImportField("brand", False, "Who makes it, e.g. Coca-Cola. Helps us match your products correctly."),
    ImportField("pack_quantity", False, "The size of one item, e.g. 2 for a 2L bottle."),
    ImportField("pack_unit", False, "The measure for pack_quantity: L, ml, kg or g."),
    *(ImportField(name, False, "Filename of a photo inside your images ZIP.") for name in IMAGE_FIELD_NAMES),
)


#: Derived, never hand-maintained.
REQUIRED_FIELD_NAMES: Tuple[str, ...] = tuple(f.name for f in IMPORT_FIELDS if f.required)
KNOWN_FIELD_NAMES: Tuple[str, ...] = tuple(f.name for f in IMPORT_FIELDS)


def field_help() -> dict:
    """name -> help text, for the template and any future mapping UI."""
    return {f.name: f.help_text for f in IMPORT_FIELDS}
