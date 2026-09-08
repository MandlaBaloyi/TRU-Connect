"""
The merchandised sections on a supplier's brand profile -- their pick,
what is on sale, what businesses buy most, what is new, what is
cheaper per unit, and any strip the supplier curated themselves.

SITS BESIDE showcase_service, NOT INSIDE IT. That module answers "here
is everything, by category"; this one answers "here is what to look at
first". They are different questions, they rank on different data, and
a supplier turns these on and off while the category strips are simply
their catalogue.

THE ORDER OF SECTIONS COMES FROM THE DATABASE, never from this file.
A wholesaler wanting their promoted range above the fold is a row
update, not a deploy -- see SupplierStorefrontSection's own docstring,
and the frontend's storefront/types.ts, which was built to render
whatever list it is handed.

A SUPPLIER WHO HAS CONFIGURED NOTHING STILL GETS A STOREFRONT. The
defaults below run for them, and no rows are written -- a business
browsing a profile must never write to that supplier's configuration
as a side effect of the read.

BROWSING STAYS OPEN, same as the rest of this package: no connection
is required to see any of this. Only ORDERING is gated
(ordering_gate.py).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from src.domains.network.connections.services.errors import SupplierNotFoundError
from src.domains.network.connections.services.storefront.product_dto import (
    build_catalog_product_dicts,
)
from src.domains.supplier.supplier_profile.models.supplier_storefront import (
    CHOSEN_SECTION_TYPES,
    StorefrontSectionType,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.domains.supplier.supplier_profile.repositories.supplier_storefront_repository import (
    SupplierStorefrontRepository,
)

#: A strip with almost nothing in it reads as a broken shelf rather
#: than a short one -- the same rule the Community feed and the app
#: itself both apply. Enforced here too so a thin section never leaves
#: the server in the first place.
MIN_PRODUCTS_PER_SECTION = 3

#: Per strip. Six is what the category showcase already uses, and a
#: horizontal rail nobody scrolls past four is not improved by twenty.
MAX_PRODUCTS_PER_SECTION = 6

#: "Just added" means recently, not ever. A supplier who last uploaded
#: eight months ago has no new arrivals, and saying otherwise would
#: make the one section whose entire claim is recency into a lie.
NEW_ARRIVAL_WINDOW_DAYS = 45

#: What a supplier gets before they have configured anything. Featured
#: and curated are absent because both need the supplier to choose
#: products -- there is nothing sensible to default them to.
DEFAULT_SECTION_ORDER = (
    StorefrontSectionType.ON_SALE,
    StorefrontSectionType.BEST_SELLERS,
    StorefrontSectionType.NEW_ARRIVALS,
    StorefrontSectionType.BULK_VALUE,
)

#: Titles for the sections the PLATFORM computes. They live here, not
#: in the database, precisely because the platform is the one making
#: the claim -- "what businesses buy most" is a statement about real
#: order data, and a supplier must not be able to reword it into
#: something the data does not support. Only CURATED is supplier-titled.
SECTION_COPY = {
    StorefrontSectionType.ON_SALE: ("On sale now", "Reduced from the usual price"),
    StorefrontSectionType.BEST_SELLERS: (
        "What businesses buy most",
        "Ordered most by businesses on TruConnect",
    ),
    StorefrontSectionType.NEW_ARRIVALS: ("Just added", "New from this supplier"),
    StorefrontSectionType.BULK_VALUE: (
        "Better per unit in bulk",
        "The more in the pack, the less each one costs",
    ),
}


def get_storefront(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    """Every section this supplier is running, in their own order.

    business_id is accepted (currently unused) for signature symmetry
    with every other business-facing read in this package.
    """
    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    # THE FALLBACK TEST IS "HAS THIS SUPPLIER CONFIGURED ANYTHING",
    # NOT "ARE ANY SECTIONS ENABLED", and a test caught the difference
    # the hard way. Reading only the ENABLED rows meant a supplier who
    # switched their one configured section OFF looked identical to a
    # supplier who had never configured anything -- so the defaults
    # kicked in and put the section they had just disabled straight
    # back on their profile. Switching something off has to mean it
    # stays off.
    #
    # Once a supplier touches their storefront at all, their
    # configuration is authoritative and the defaults stop applying.
    configured = SupplierStorefrontRepository.list_all_for_supplier(supplier_profile_id)
    rows = [row for row in configured if row.is_enabled] if configured else _default_rows()

    sections: List[dict] = []
    for row in rows:
        built = _build_section(supplier_profile_id, row)
        if built is not None:
            sections.append(built)

    return {"sections": sections}


class _DefaultRow:
    """Stands in for a database row for a supplier who has configured
    nothing. Deliberately NOT a real row written on read -- see this
    module's own docstring on why a business browsing must not write to
    the supplier's configuration."""

    id = None
    title = None
    subtitle = None

    def __init__(self, section_type: StorefrontSectionType, position: int):
        self.section_type = section_type
        self.position = position


def _default_rows() -> List[_DefaultRow]:
    return [_DefaultRow(section_type, index) for index, section_type in enumerate(DEFAULT_SECTION_ORDER)]


def _build_section(supplier_profile_id: str | UUID, row) -> Optional[dict]:
    """One section, or None when it has nothing worth showing.

    RETURNING None IS THE NORMAL CASE, not an error. A supplier running
    no promotions has no sale strip; one who uploaded nothing this
    month has no new arrivals. The section simply does not appear, and
    the profile is shorter -- which is the honest outcome, and the same
    "silence is the honest answer" rule the track record follows.
    """
    section_type = row.section_type

    if section_type in CHOSEN_SECTION_TYPES:
        products = SupplierStorefrontRepository.list_products_for_section(row.id) if row.id else []
    else:
        products = _query_computed_products(supplier_profile_id, section_type)

    # A featured pick is one product by definition -- the minimum that
    # protects a RAIL from looking broken does not apply to it.
    minimum = 1 if section_type == StorefrontSectionType.FEATURED_PRODUCT else MIN_PRODUCTS_PER_SECTION
    if len(products) < minimum:
        return None

    products = products[:MAX_PRODUCTS_PER_SECTION]
    product_dicts = build_catalog_product_dicts(products)

    if section_type == StorefrontSectionType.FEATURED_PRODUCT:
        return {
            "id": str(row.id),
            "type": section_type.value,
            "label": "Supplier's pick",
            "product": product_dicts[0],
        }

    if section_type == StorefrontSectionType.CURATED:
        return {
            "id": str(row.id),
            "type": section_type.value,
            # The supplier's own words, with a fallback rather than a
            # crash: a strip whose title was never set is a
            # configuration mistake, not a reason to break their profile.
            "title": row.title or "Picked by this supplier",
            # The supplier's own second line, when they wrote one. The
            # computed sections get platform-written subtitles because
            # the platform is making the claim; a shelf is the one
            # section where the supplier explains their own choice.
            "subtitle": row.subtitle,
            "products": product_dicts,
        }

    title, subtitle = SECTION_COPY[section_type]
    return {
        "id": str(row.id) if row.id else f"default-{section_type.value.lower()}",
        "type": section_type.value,
        "title": title,
        "subtitle": subtitle,
        "products": product_dicts,
    }


def _query_computed_products(supplier_profile_id: str | UUID, section_type: StorefrontSectionType) -> List:
    """The four sections the platform derives itself.

    EVERY ONE EXCLUDES ARCHIVED PRODUCTS, and none of them excludes
    out-of-stock ones. That asymmetry is deliberate: an archived
    product is gone, while an out-of-stock product is real, still worth
    seeing, and every storefront card already has an explicit
    out-of-stock state. Hiding it would also make "what businesses buy
    most" quietly wrong -- popularity and availability are different
    facts.
    """
    from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository

    if section_type == StorefrontSectionType.ON_SALE:
        return SupplierOfferRepository.list_on_sale(supplier_profile_id, limit=MAX_PRODUCTS_PER_SECTION)

    if section_type == StorefrontSectionType.BEST_SELLERS:
        return SupplierOfferRepository.list_best_selling(supplier_profile_id, limit=MAX_PRODUCTS_PER_SECTION)

    if section_type == StorefrontSectionType.NEW_ARRIVALS:
        since = datetime.now(timezone.utc) - timedelta(days=NEW_ARRIVAL_WINDOW_DAYS)
        return SupplierOfferRepository.list_recently_added(
            supplier_profile_id, since=since, limit=MAX_PRODUCTS_PER_SECTION
        )

    if section_type == StorefrontSectionType.BULK_VALUE:
        return SupplierOfferRepository.list_best_unit_value(
            supplier_profile_id, limit=MAX_PRODUCTS_PER_SECTION
        )

    return []
