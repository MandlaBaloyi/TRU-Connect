"""
The product taxonomy -- categories and units.

MOVED HERE FROM supplier/products IN V2 STEP 2, and the move is the
point rather than tidying. A category is a fact about a PRODUCT ("this
is a beverage"), not about one supplier's offer of it. Two suppliers
selling the same case of Coke do not get to disagree about what
category it is.

Leaving these in the supplier domain would have forced the catalogue to
import from supplier, which is backwards: an offer references a
catalogue product, so supplier depends on catalogue and never the
reverse.

THE POSTGRES TYPES DELIBERATELY DID NOT MOVE. Both enums are still
declared to SQLAlchemy as name="product_category" / name="product_unit"
in the `supplier` SCHEMA, because that is where the existing types live
and every existing column already points at them. Moving a Postgres
enum type between schemas means dropping and recreating it with every
dependent column rewritten -- real risk, on live data, for a cosmetic
gain. The Python class moved; the database type stays until there is a
reason worth that migration.

So a catalogue table using `supplier.product_category` looks odd and is
correct. When the catalogue becomes authoritative for categories -- when
offers stop carrying their own and read the product's instead -- the
type moves schema in that same change, where it belongs.
"""
from __future__ import annotations

import enum


class ProductCategory(str, enum.Enum):
    """TRU-Connect-controlled taxonomy, matching the frontend's own
    CATEGORY_OPTIONS exactly (16 values). Every member's NAME equals
    its VALUE (e.g. BEVERAGES = "BEVERAGES") -- deliberately, not by
    accident: SQLAlchemy's Enum(PyEnumClass) persists the member's
    .name to Postgres, not its .value. This codebase already hit that
    exact mismatch once (ConnectionRequestStatus, whose lowercase
    values differ from its uppercase names, needed the Postgres enum's
    stored values corrected to match what actually gets persisted).
    Keeping name == value here sidesteps that whole class of bug by
    construction, and it also means the string this returns over the
    API is exactly what the frontend's own ProductCategory union
    expects -- no lowercase/uppercase translation layer needed
    anywhere.
    """

    FOOD_GROCERY = "FOOD_GROCERY"
    BEVERAGES = "BEVERAGES"
    SNACKS_CONFECTIONERY = "SNACKS_CONFECTIONERY"
    BAKERY = "BAKERY"
    DAIRY_CHILLED = "DAIRY_CHILLED"
    FRESH_PRODUCE = "FRESH_PRODUCE"
    MEAT_FROZEN = "MEAT_FROZEN"
    HOUSEHOLD_CLEANING = "HOUSEHOLD_CLEANING"
    PERSONAL_CARE = "PERSONAL_CARE"
    # Hair, wigs, braids, relaxers, cosmetics, nails. SEPARATE FROM
    # PERSONAL_CARE deliberately: that is soap and toothpaste, bought
    # from a different supplier on a different rhythm. Folding the two
    # together would put a salon's stock behind a grocery wholesaler.
    BEAUTY_HAIR = "BEAUTY_HAIR"
    BABY_FAMILY = "BABY_FAMILY"
    STATIONERY_SCHOOL = "STATIONERY_SCHOOL"
    HARDWARE_GENERAL = "HARDWARE_GENERAL"
    ELECTRONICS_ACCESSORIES = "ELECTRONICS_ACCESSORIES"
    PACKAGING_DISPOSABLE = "PACKAGING_DISPOSABLE"
    CLOTHING_APPAREL = "CLOTHING_APPAREL"
    OTHER = "OTHER"


class ProductUnit(str, enum.Enum):
    """Matches the frontend's own UNIT_OPTIONS exactly (12 values).
    Same name==value convention as ProductCategory, same reasoning.
    Used for BOTH selling_unit and unit_measure -- one enum, two
    columns, matching the frontend's own single ProductUnit type
    serving both roles."""

    EACH = "EACH"
    PACK = "PACK"
    BOX = "BOX"
    CASE = "CASE"
    BAG = "BAG"
    BOTTLE = "BOTTLE"
    CAN = "CAN"
    DOZEN = "DOZEN"
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"


#: The schema the Postgres enum TYPES live in -- see this module's
#: docstring. Referenced by every db.Enum(...) that uses these, so the
#: day the types do move there is one constant to change rather than a
#: search across two domains.
TAXONOMY_TYPE_SCHEMA = "supplier"


#: HOW A CATEGORY IS SHOWN: the label a person reads, and the lucide
#: icon name the app resolves.
#:
#: SERVER-SIDE BECAUSE THE FEED CONTRACT SAYS SO. FeedCategory.icon is
#: documented as "server-chosen so a new category doesn't need an app
#: release to get an icon" -- that is the whole reason it is a string on
#: the wire rather than something the app looks up.
#:
#: THE APP STILL KEEPS ITS OWN MAP, and that is not duplication for its
#: own sake: components/categories/CategoryIcon.tsx is a
#: Record<ProductCategory, Icon>, so a value added to the enum without
#: an icon is a COMPILE ERROR there. Belt and braces, each catching what
#: the other cannot -- the app's map catches a forgotten icon at build
#: time, and this one lets a brand-new category get a sensible icon on a
#: phone that has not been updated yet. The app prefers this name and
#: falls back to its own.
CATEGORY_DISPLAY: dict[ProductCategory, tuple[str, str]] = {
    ProductCategory.FOOD_GROCERY: ("Food & Grocery", "ShoppingBasket"),
    ProductCategory.BEVERAGES: ("Beverages", "CupSoda"),
    ProductCategory.SNACKS_CONFECTIONERY: ("Snacks & Confectionery", "Candy"),
    ProductCategory.BAKERY: ("Bakery", "Croissant"),
    ProductCategory.DAIRY_CHILLED: ("Dairy & Chilled", "Milk"),
    ProductCategory.FRESH_PRODUCE: ("Fresh Produce", "Carrot"),
    ProductCategory.MEAT_FROZEN: ("Meat & Frozen", "Beef"),
    ProductCategory.HOUSEHOLD_CLEANING: ("Household & Cleaning", "SprayCan"),
    ProductCategory.PERSONAL_CARE: ("Personal Care", "ShowerHead"),
    ProductCategory.BEAUTY_HAIR: ("Beauty & Hair", "Brush"),
    ProductCategory.BABY_FAMILY: ("Baby & Family", "Baby"),
    ProductCategory.STATIONERY_SCHOOL: ("Stationery & School", "PencilRuler"),
    ProductCategory.HARDWARE_GENERAL: ("Hardware & General", "Hammer"),
    ProductCategory.ELECTRONICS_ACCESSORIES: ("Electronics & Accessories", "Smartphone"),
    ProductCategory.PACKAGING_DISPOSABLE: ("Packaging & Disposable", "Package"),
    ProductCategory.CLOTHING_APPAREL: ("Clothing & Apparel", "Shirt"),
    ProductCategory.OTHER: ("Other", "Shapes"),
}
