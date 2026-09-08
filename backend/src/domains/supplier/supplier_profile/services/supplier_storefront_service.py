"""
The SUPPLIER's own side of their storefront: which of the six sections
run, in what order, and -- for the two the platform cannot compute --
which products are in them.

THE MIRROR OF connections' storefront_sections_service, which is what a
BUSINESS sees. This one never builds products or ranks anything; it
only reads and writes configuration. The split matters: a supplier
editing their shopfront and a business browsing it are different
domains with different auth, and the business-facing service must never
grow a write path.

WRITES REPLACE THE WHOLE CONFIGURATION, deliberately -- one PUT with
the full list rather than a dozen small endpoints for toggling,
reordering, retitling and picking. Reordering is inherently about the
whole set (moving one section changes every position after it), so a
per-section endpoint would have the client sending several requests
that are only correct together. It also matches how
supplier_profile_service already handles the profile itself.
"""
from __future__ import annotations

from typing import Iterable, List
from uuid import UUID

from src.core.exceptions import NotFoundError
from src.domains.supplier.products.repositories.supplier_offer_repository import SupplierOfferRepository
from src.domains.supplier.supplier_profile.models.supplier_storefront import (
    CHOSEN_SECTION_TYPES,
    StorefrontSectionType,
    SupplierStorefrontSection,
    SupplierStorefrontSectionProduct,
)
from src.domains.supplier.supplier_profile.repositories.supplier_storefront_repository import (
    SupplierStorefrontRepository,
)
from src.domains.supplier.supplier_profile.services.errors import ProfileValidationError
from src.extensions import db

#: A curated strip is a rail; below this it reads as a broken shelf
#: rather than a short one, and the business-facing service would drop
#: it anyway. Refusing it here means the supplier finds out while
#: building it, not by wondering why it never appeared.
MIN_CURATED_PRODUCTS = 3

#: Per strip -- the same ceiling the business-facing service renders.
MAX_SECTION_PRODUCTS = 6

#: A supplier's own shelves. More than a handful stops being
#: merchandising and becomes a second catalogue, and every one of them
#: pushes the supplier's real categories further down their profile --
#: five is enough for a seasonal shelf, a promo shelf and a couple of
#: standing ones without burying anything.
MAX_CURATED_SECTIONS = 5

#: A second line under a shelf's title. Optional -- a good title often
#: needs no explaining, and forcing one would just produce filler.
MAX_SUBTITLE_LENGTH = 80


def get_configuration(supplier_profile_id: str | UUID) -> dict:
    """Everything the supplier's own storefront screen needs --
    INCLUDING sections they have switched off, which a business would
    never be sent. A disabled section still has to appear here, or
    there is no way to switch it back on."""
    rows = SupplierStorefrontRepository.list_all_for_supplier(supplier_profile_id)
    by_type = {row.section_type: row for row in rows if row.section_type not in CHOSEN_SECTION_TYPES}

    sections: List[dict] = []

    # THE FOUR COMPUTED SECTIONS ARE ALWAYS LISTED, configured or not.
    # A supplier who has never touched this screen still needs to see
    # all four with their real default state, rather than an empty
    # screen that implies they have no storefront at all.
    for section_type in (
        StorefrontSectionType.ON_SALE,
        StorefrontSectionType.BEST_SELLERS,
        StorefrontSectionType.NEW_ARRIVALS,
        StorefrontSectionType.BULK_VALUE,
    ):
        row = by_type.get(section_type)
        sections.append(
            {
                "type": section_type.value,
                "isEnabled": row.is_enabled if row else True,
                "position": row.position if row else len(sections),
                "isComputed": True,
                "title": None,
                "subtitle": None,
                "productIds": [],
            }
        )

    for row in rows:
        if row.section_type not in CHOSEN_SECTION_TYPES:
            continue
        products = SupplierStorefrontRepository.list_products_for_section(row.id)
        sections.append(
            {
                "id": str(row.id),
                "type": row.section_type.value,
                "isEnabled": row.is_enabled,
                "position": row.position,
                "isComputed": False,
                "title": row.title,
                "subtitle": row.subtitle,
                "productIds": [str(product.id) for product in products],
            }
        )

    sections.sort(key=lambda section: section["position"])
    return {"sections": sections}


def replace_configuration(supplier_profile_id: str | UUID, sections: Iterable[dict]) -> dict:
    """Replace the whole storefront configuration in one write.

    VALIDATES BEFORE IT DELETES ANYTHING. Every section and every
    product id is checked first, and only then are the old rows
    replaced -- otherwise a bad product id halfway through would leave
    a supplier with half a storefront and no way to tell what happened.
    """
    incoming = list(sections)
    _validate(supplier_profile_id, incoming)

    # Soft-delete the old configuration rather than mutating it in
    # place: positions and section identities shift around freely when
    # a supplier reorders, and matching old rows to new ones would be
    # guesswork. BaseModel's is_deleted keeps the history.
    for row in SupplierStorefrontRepository.list_all_for_supplier(supplier_profile_id):
        for link in SupplierStorefrontSectionProduct.query.filter_by(section_id=row.id).all():
            link.is_deleted = True
        row.is_deleted = True

    for position, section in enumerate(incoming):
        section_type = StorefrontSectionType(section["type"])
        row = SupplierStorefrontSection(
            supplier_profile_id=supplier_profile_id,
            section_type=section_type,
            is_enabled=bool(section.get("isEnabled", True)),
            position=position,
            title=(section.get("title") or None) if section_type == StorefrontSectionType.CURATED else None,
            subtitle=(section.get("subtitle") or None)
            if section_type == StorefrontSectionType.CURATED
            else None,
        )
        db.session.add(row)
        db.session.flush()  # need row.id for the product links below

        if section_type in CHOSEN_SECTION_TYPES:
            for index, product_id in enumerate(section.get("productIds") or []):
                db.session.add(
                    SupplierStorefrontSectionProduct(
                        section_id=row.id, product_id=product_id, position=index
                    )
                )

    db.session.commit()
    return get_configuration(supplier_profile_id)


def _validate(supplier_profile_id: str | UUID, sections: List[dict]) -> None:
    seen_computed = set()
    curated_count = 0

    for section in sections:
        try:
            section_type = StorefrontSectionType(section.get("type"))
        except ValueError:
            raise ProfileValidationError(
                "That isn't a storefront section.",
                errors=[f"Unknown section type: {section.get('type')!r}."],
            )

        if section_type not in CHOSEN_SECTION_TYPES:
            # ONE OF EACH COMPUTED TYPE. Two "on sale" strips would be
            # the same query twice, and the second would be identical
            # to the first -- there is no second set of discounted
            # products to put in it.
            if section_type in seen_computed:
                raise ProfileValidationError(
                    "You can only have one of each of those sections.",
                    errors=[f"{section_type.value} appears more than once."],
                )
            seen_computed.add(section_type)
            continue

        product_ids = section.get("productIds") or []

        if section_type == StorefrontSectionType.FEATURED_PRODUCT:
            if len(product_ids) != 1:
                raise ProfileValidationError(
                    "Your featured pick has to be exactly one product.",
                    errors=["Choose a single product to feature."],
                )
        else:
            curated_count += 1
            if curated_count > MAX_CURATED_SECTIONS:
                raise ProfileValidationError(
                    f"You can run up to {MAX_CURATED_SECTIONS} of your own shelves.",
                    errors=["Remove one before adding another."],
                )
            if not (section.get("title") or "").strip():
                raise ProfileValidationError(
                    "Give your shelf a name.",
                    errors=["A shelf a business sees needs a title, like 'Stock up for month-end'."],
                )
            if len((section.get("subtitle") or "").strip()) > MAX_SUBTITLE_LENGTH:
                raise ProfileValidationError(
                    "That second line is too long.",
                    errors=[f"Keep it under {MAX_SUBTITLE_LENGTH} characters."],
                )
            if len(product_ids) < MIN_CURATED_PRODUCTS:
                raise ProfileValidationError(
                    f"Pick at least {MIN_CURATED_PRODUCTS} products for your shelf.",
                    errors=["A shelf with fewer than that looks broken rather than short."],
                )

        if len(product_ids) > MAX_SECTION_PRODUCTS:
            raise ProfileValidationError(
                f"A section shows up to {MAX_SECTION_PRODUCTS} products.",
                errors=["Remove a few and the rest will still be there."],
            )

        if len(set(product_ids)) != len(product_ids):
            raise ProfileValidationError(
                "The same product is on that shelf twice.",
                errors=["Each product can appear once per shelf."],
            )

        _assert_products_are_sellable(supplier_profile_id, product_ids)


def _assert_products_are_sellable(supplier_profile_id: str | UUID, product_ids: List[str]) -> None:
    """Every id must be one of THIS supplier's own live products.

    THE OWNERSHIP CHECK IS THE POINT. Without it a supplier could put
    a competitor's product id into their own strip, and the
    business-facing service would happily render it on their profile --
    complete with the other supplier's price. Archived products are
    refused for a plainer reason: the strip would silently drop them
    when a business looked, and the supplier would never know why.
    """
    if not product_ids:
        return

    found = SupplierOfferRepository.list_by_ids_and_supplier(product_ids, supplier_profile_id)
    found_by_id = {str(product.id): product for product in found}

    for product_id in product_ids:
        product = found_by_id.get(str(product_id))
        if product is None:
            raise NotFoundError("One of those products isn't yours.", code="PRODUCT_NOT_FOUND")
        if product.is_archived:
            raise ProfileValidationError(
                f"'{product.name}' is archived.",
                errors=["Unarchive it first, or choose a different product."],
            )
