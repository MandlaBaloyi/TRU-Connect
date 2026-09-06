"""
Discovery -- searching for the other party and viewing their profile,
both directions (a business searches suppliers / Find Supplier; a
supplier searches businesses / Find Business), plus the shared
photo-settings write.

search never returns more than to_search_result_dict already narrows
it to; a profile view never returns more than to_profile_preview_dict
plus the deliberately-ungated brand assets and the connection-gated
contact block. See _common.py for the authorization / privacy framing
shared across every connections service module.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from src.domains.network.connections.models.connection_request import ConnectionRequestStatus
from src.domains.network.connections.repositories.connection_request_repository import (
    ConnectionRequestRepository,
)
from src.domains.network.connections.services._common import (
    _dispatch_search,
    _resolve_supplier_profile_id,
    _resolve_visible_photo_url,
)
from src.domains.network.connections.services.errors import (
    BusinessNotFoundError,
    SupplierNotFoundError,
)
from src.domains.supplier.supplier_profile.repositories.supplier_profile_repository import (
    SupplierProfileRepository,
)
from src.extensions import db


# ---------------------------------------------------------------------------
# Business searches Suppliers -- Find Supplier, the original direction.
# ---------------------------------------------------------------------------


def search_suppliers(query: str, business_id: str | UUID) -> list[dict]:
    from src.domains.auth.models.user import User

    def resolve_photo(supplier_profile) -> str | None:
        connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile.id)
        is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE
        supplier_user = User.query.filter_by(id=supplier_profile.supplier_id).first()
        personal_photo_url = supplier_user.profile_image_url if supplier_user else None
        return _resolve_visible_photo_url(
            supplier_profile, personal_photo_url=personal_photo_url, is_active_connection=is_active
        )

    return _dispatch_search(query, SupplierProfileRepository, resolve_photo=resolve_photo)


# A supplier needs a real track record before any of it is shown. Below
# this, "accepted 1 of 1 order" reads as a statistic when it's a
# coincidence -- and an unlucky first decline would brand a good
# supplier permanently. Silence is the honest answer for a new supplier,
# not a flattering number built on nothing.
MIN_DECIDED_ORDERS_FOR_RELIABILITY = 5


def _resolve_reliability(supplier_profile_id: str | UUID) -> Optional[dict]:
    """None until there's enough history to be meaningful -- see
    MIN_DECIDED_ORDERS_FOR_RELIABILITY. The frontend renders nothing at
    all for None rather than an empty or zeroed block."""
    from src.domains.network.orders.repositories.stock_order_repository import StockOrderRepository

    stats = StockOrderRepository.reliability_stats_for_supplier(supplier_profile_id)
    if stats["decidedCount"] < MIN_DECIDED_ORDERS_FOR_RELIABILITY:
        return None
    return {
        "decidedCount": stats["decidedCount"],
        "acceptedCount": stats["acceptedCount"],
        "medianResponseHours": stats["medianResponseHours"],
    }


def get_supplier_profile(business_id: str | UUID, supplier_profile_id: str | UUID) -> dict:
    from src.domains.auth.models.user import User
    from src.domains.supplier.products.repositories.product_repository import ProductRepository

    supplier = SupplierProfileRepository.get_by_id(supplier_profile_id)
    if not supplier:
        raise SupplierNotFoundError("Supplier not found.")

    connection = ConnectionRequestRepository.get_for_business_and_supplier(business_id, supplier_profile_id)
    connection_status = connection.status.value.upper() if connection else "NOT_REQUESTED"
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    supplier_user = User.query.filter_by(id=supplier.supplier_id).first()
    personal_photo_url = supplier_user.profile_image_url if supplier_user else None
    visible_photo_url = _resolve_visible_photo_url(
        supplier, personal_photo_url=personal_photo_url, is_active_connection=is_active
    )

    profile = supplier.to_profile_preview_dict(connection_status, visible_photo_url)
    profile["productCount"] = ProductRepository.count_for_supplier(supplier_profile_id)

    # Brand assets -- deliberately UNGATED, unlike photoUrl above.
    # A supplier's business photo and cover banner are their public
    # shopfront: a business deciding whether to connect needs to see
    # them regardless of connection status (the whole point of the
    # brand-awareness profile). The PERSONAL photo stays behind
    # _resolve_visible_photo_url's connection gate; these two do not.
    profile["businessImageUrl"] = supplier.business_image_url
    profile["coverImageUrl"] = supplier.cover_image_url

    # Fulfilment terms -- ALSO deliberately ungated, same reasoning as
    # the brand assets above: "do you deliver" and "what's your minimum
    # order" are exactly what a business needs while DECIDING whether
    # to connect. Gating them behind an active connection would mean
    # discovering the supplier can't serve you only after building a
    # cart. Contrast collectionAddress below, which is a real street
    # address and stays connection-only.
    profile["offersDelivery"] = supplier.offers_delivery
    profile["minimumOrderCents"] = supplier.minimum_order_cents

    # ---- SOCIAL PROOF + REAL TRACK RECORD, all ungated ----------------
    # A business deciding whether to trust a stranger with money is
    # asking "do other businesses buy here, and do orders actually go
    # through". Both are answered from data TruConnect already holds --
    # no self-reported claims, no reviews to game.
    profile["connectedBusinessCount"] = ConnectionRequestRepository.count_active_for_supplier_profile(
        supplier_profile_id
    )
    profile["reliability"] = _resolve_reliability(supplier_profile_id)
    # The categories this supplier ACTUALLY stocks, as chips under their
    # name. Self-correcting where a supplier's own description drifts
    # from what they sell (a real case: a bio about fragrances above a
    # shop full of cold drinks and chips).
    profile["stockedCategories"] = ProductRepository.list_distinct_categories_for_supplier(supplier_profile_id)

    # WHO asked whom. connectionStatus alone can't answer "am I waiting
    # on them, or are they waiting on me" -- a PENDING request reads
    # completely differently depending on which side started it (see
    # ConnectionInitiatorRole). Null whenever there's no request at all.
    profile["connectionInitiatedBy"] = (
        connection.initiated_by_role.value.upper() if connection and connection.initiated_by_role else None
    )

    # Same gate as list_supplier_products'/get_supplier_product's own
    # contact block -- is_active AND the supplier's own opt-in. Added
    # here specifically so a business viewing an order they can no
    # longer self-cancel (already CONFIRMED) has a real way to
    # actually reach the supplier, not a dead-end message.
    profile["contact"] = None
    if is_active and supplier.share_contact_details:
        profile["contact"] = {
            "whatsappNumber": supplier.whatsapp_number,
            "email": supplier.contact_email,
            "tiktokHandle": supplier.tiktok_handle,
        }

    # Gated by is_active ONLY -- deliberately NOT also behind
    # share_contact_details like whatsapp/email above. Those are
    # optional extra communication channels a supplier might not want
    # to hand out; a collection address is core functional
    # information an actively-connected business needs to actually
    # complete a COLLECT order, not a discretionary opt-in.
    profile["collectionAddress"] = None
    if is_active and (supplier.collection_street or supplier.collection_suburb):
        profile["collectionAddress"] = {
            "building": supplier.collection_building,
            "street": supplier.collection_street,
            "suburb": supplier.collection_suburb,
            "city": supplier.collection_city,
            "province": supplier.collection_province,
            "postalCode": supplier.collection_postal_code,
            "latitude": float(supplier.collection_latitude) if supplier.collection_latitude is not None else None,
            "longitude": float(supplier.collection_longitude) if supplier.collection_longitude is not None else None,
        }

    return profile


# ---------------------------------------------------------------------------
# Supplier searches Businesses -- Find Business, the reverse direction.
# Model/repository layer (BusinessProfile.normalized_phone/normalized_email,
# BusinessProfileRepository.search_by_*) was already built anticipating
# this; only this service layer and the routes are new.
# ---------------------------------------------------------------------------


def search_businesses(query: str, supplier_id: str | UUID) -> list[dict]:
    from src.domains.auth.models.user import User
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)

    def resolve_photo(business_profile) -> str | None:
        connection = ConnectionRequestRepository.get_for_business_and_supplier(
            business_profile.business_id, supplier_profile_id
        )
        is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE
        business_user = User.query.filter_by(id=business_profile.business_id).first()
        personal_photo_url = business_user.profile_image_url if business_user else None
        return _resolve_visible_photo_url(
            business_profile, personal_photo_url=personal_photo_url, is_active_connection=is_active
        )

    return _dispatch_search(query, BusinessProfileRepository, resolve_photo=resolve_photo)


def get_business_profile(supplier_id: str | UUID, business_profile_id: str | UUID) -> dict:
    from src.domains.auth.models.user import User
    from src.domains.business.business_profile.repositories.business_profile_repository import (
        BusinessProfileRepository,
    )

    business_profile = BusinessProfileRepository.get_by_id(business_profile_id)
    if not business_profile:
        raise BusinessNotFoundError("Business not found.")

    supplier_profile_id = _resolve_supplier_profile_id(supplier_id)
    connection = ConnectionRequestRepository.get_for_business_and_supplier(
        business_profile.business_id, supplier_profile_id
    )
    connection_status = connection.status.value.upper() if connection else "NOT_REQUESTED"
    is_active = connection is not None and connection.status == ConnectionRequestStatus.ACTIVE

    business_user = User.query.filter_by(id=business_profile.business_id).first()
    personal_photo_url = business_user.profile_image_url if business_user else None
    visible_photo_url = _resolve_visible_photo_url(
        business_profile, personal_photo_url=personal_photo_url, is_active_connection=is_active
    )

    return business_profile.to_profile_preview_dict(connection_status, visible_photo_url)


# ---------------------------------------------------------------------------
# Photo settings -- which image shows, and to whom. Shared function for
# both roles: how a profile presents itself to the network is genuinely
# one concern, not two role-specific mirrors -- both SupplierProfile and
# BusinessProfile carry the identical three fields (see their own model
# docstrings). This is the WRITE side of what _resolve_visible_photo_url
# reads.
# ---------------------------------------------------------------------------


def update_my_photo_settings(
    user_id: str | UUID,
    user_role: str,
    *,
    visible_image_source: str | None = None,
    photo_visibility: str | None = None,
) -> dict:
    """Only the fields actually provided get changed -- either
    parameter left as None leaves that setting untouched."""
    if user_role == "supplier":
        from src.domains.supplier.supplier_profile.models.supplier_profile import (
            PhotoVisibility,
            VisibleImageSource,
        )

        profile = SupplierProfileRepository.get_or_create_for_supplier(user_id)
    else:
        from src.domains.business.business_profile.models.business_profile import (
            PhotoVisibility,
            VisibleImageSource,
        )
        from src.domains.business.business_profile.repositories.business_profile_repository import (
            BusinessProfileRepository,
        )

        profile = BusinessProfileRepository.get_or_create_for_business(user_id)

    if visible_image_source is not None:
        profile.visible_image_source = VisibleImageSource(visible_image_source)
    if photo_visibility is not None:
        profile.photo_visibility = PhotoVisibility(photo_visibility)

    db.session.commit()

    return {
        "visibleImageSource": profile.visible_image_source.value,
        "photoVisibility": profile.photo_visibility.value,
    }
