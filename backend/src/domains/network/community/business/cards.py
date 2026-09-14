"""
Turning rows into the card shapes the app already renders.

SPLIT OUT OF sections.py for the same reason as queries.py: a builder
should read as "what goes in this rail and why", not as field mapping.

NOTHING HERE DECIDES WHAT APPEARS -- only how it looks once something
else has decided. That separation is what lets a section change its mind
about which products to show without touching a single field name.
Same underscore note as queries.py: these are a module's public
surface now, so they are named like one.
"""
from __future__ import annotations

from typing import List, Optional

# feed_suppliers batches ONE lookup for a whole rail rather than
# asking per card. The query itself lives with the other queries; a
# card module reading from a query module is the normal direction.
from src.domains.network.community.business.queries import last_active_map

def feed_products(pairs: List) -> List[dict]:
    """SupplierOffer rows in the shape the app's product cards render.

    Reuses build_catalog_product_dicts for the parts that are easy to
    get subtly wrong -- batched inventory rather than a query per
    product, and APPROVED-only media -- then maps to the feed's own
    flatter shape, which carries the supplier on every card because a
    feed rail mixes suppliers where a shopfront never does.
    """
    from src.domains.network.connections.services.storefront.product_dto import (
        build_catalog_product_dicts,
    )

    from src.shared.algorithms import social_proof
    from src.domains.network.orders.repositories.stock_order_repository import (
        StockOrderRepository,
    )

    offers = [pair[0] for pair in pairs]
    enriched = build_catalog_product_dicts(offers)

    # ONE COUNT QUERY FOR THE WHOLE RAIL, not one per card. The number
    # itself is the most persuasive thing on the card (social_proof.py);
    # fetching it per product would be the N+1 this package has removed
    # twice already.
    buyer_counts = StockOrderRepository.buyer_counts_for_products(
        [offer.id for offer in offers]
    )

    feed_products = []

    for (offer, supplier_name, verification_status), dto in zip(pairs, enriched):
        supplier_id = offer.supplier_profile_id
        images = dto.get("images") or []
        feed_products.append(
            {
                "id": dto["id"],
                "supplierId": str(supplier_id),
                "supplierName": supplier_name,
                # THE TICK TRAVELS WITH THE NAME, on every surface that
                # prints one. On a feed rail it is always true (the
                # curtain got here first), and that is exactly why it
                # must be present: a name WITHOUT a tick reads as a
                # statement, so a card that simply forgot to send the
                # field would look like an accusation.
                "supplierVerificationStatus": (
                    verification_status.value
                    if hasattr(verification_status, "value")
                    else verification_status
                ),
                "name": dto["name"],
                # ONE image, not the gallery: a rail card shows a
                # thumbnail, and shipping four URLs per card to render
                # one is bandwidth a spaza shop pays for.
                "imageUrl": (images[0].get("url") if isinstance(images[0], dict) else images[0])
                if images
                else None,
                "priceCents": dto["priceCents"],
                "compareAtPriceCents": dto["compareAtPriceCents"],
                "unitLabel": unit_label(dto),
                "inStock": dto["inStock"],
                # WHAT OTHER SHOPS DID -- the one claim on this card
                # that is neither our opinion nor the supplier's. None
                # when nobody has bought it yet: a "0 businesses bought
                # this" badge is true, useless, and reads as a warning.
                "buyerCount": buyer_counts.get(offer.id) or None,
                "buyerLabel": social_proof.label(buyer_counts.get(offer.id)),
            }
        )
    return feed_products


def unit_label(dto: dict) -> Optional[str]:
    """"each", "case of 12", "bag of 10kg".

    BUILT SERVER-SIDE because the feed contract says so, and because the
    three columns it is built from (selling unit, quantity, measure) are
    exactly the ones that were never sent to a business before -- a pack
    of 6 and a pack of 24 looked identical at the same price.
    """
    unit = (dto.get("sellingUnit") or "").lower()
    quantity = dto.get("unitQuantity")
    measure = (dto.get("unitMeasure") or "").lower() if dto.get("unitMeasure") else None

    if not unit:
        return None
    if unit == "each" or not quantity:
        return unit
    if measure:
        return f"{unit} of {quantity}{measure}"
    return f"{unit} of {quantity}"


def feed_supplier(
    profile,
    distance_km: Optional[float] = None,
    last_active_at=None,
    is_connected: bool = False,
) -> dict:
    """The supplier card shape, ungated brand assets only.

    NO STREET ADDRESS, ever -- `location` is suburb or city, the same
    rule the search results follow. A discovery rail is seen by people
    with no relationship to this supplier.
    """
    return {
        "id": str(profile.id),
        "businessName": profile.business_name,
        "businessImageUrl": profile.business_image_url,
        "coverImageUrl": profile.cover_image_url,
        "category": profile.category,
        "location": profile.location,
        "verificationStatus": (
            profile.verification_status.value if profile.verification_status else None
        ),
        "offersDelivery": profile.offers_delivery,
        "minimumOrderCents": profile.minimum_order_cents,
        "distanceKm": distance_km,
        # THE CARD ALREADY HAD A BADGE FOR THIS and nothing ever set
        # it. Now that discovery rails show connected suppliers
        # rather than hiding them, it is the field that tells a shop
        # which of these they already deal with.
        "isConnected": is_connected,
        # FROM THE SUPPLIER'S USER ROW, not the profile -- the heartbeat
        # lives on auth.users -- and only when they have chosen to show
        # it. Passed in rather than looked up here so the caller can
        # batch one query for the whole rail instead of one per card.
        "lastActiveAt": last_active_at.isoformat() if last_active_at else None,
    }


def feed_suppliers(
    profiles: List,
    distances: Optional[dict] = None,
    connected_ids: Optional[set] = None,
) -> List[dict]:
    """Every supplier card in a rail, with the activity lookup batched."""
    seen = last_active_map(profiles)
    return [
        feed_supplier(
            p,
            distance_km=(distances or {}).get(p.id),
            last_active_at=seen.get(p.id),
            is_connected=str(p.id) in (connected_ids or set()),
        )
        for p in profiles
    ]


def nearest_subtitle(profile) -> Optional[str]:
    """"Closest to Soweto" -- the business's own suburb, not a distance.

    A number here would be the distance to the FIRST card, which stops
    being true as soon as the reader scrolls.
    """
    where = profile.city_or_town
    return f"Closest to {where}" if where else None
