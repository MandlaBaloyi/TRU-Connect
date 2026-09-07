"""
supplier_profile's own request schemas -- shape validation only (real
business rules live in supplier_profile_service.py, same split as
every other domain's schemas/ vs services/ in this codebase).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate

from src.domains.supplier.supplier_profile.models.supplier_profile_image import ProfileImageSlot

_SLOT_VALUES = [s.value for s in ProfileImageSlot]


class ProfileImageSignatureSchema(Schema):
    """Body of POST /my-profile/images/upload-signature -- just the
    slot; everything else the client needs comes back in the signed
    response."""

    slot = fields.Str(required=True, validate=validate.OneOf(_SLOT_VALUES))


class RegisterProfileImageSchema(Schema):
    """Body of POST /my-profile/images -- shape mirrors products'
    RegisterMediaSchema exactly, plus the slot. Ownership (is this
    public_id actually one this backend signed for this supplier?) is
    the service's job, not this schema's."""

    slot = fields.Str(required=True, validate=validate.OneOf(_SLOT_VALUES))
    cloudinary_public_id = fields.Str(required=True)
    secure_url = fields.Str(required=True)
    resource_type = fields.Str(required=False, load_default="image")
    format = fields.Str(required=False, allow_none=True, load_default=None)
    width = fields.Integer(required=False, allow_none=True, load_default=None)
    height = fields.Integer(required=False, allow_none=True, load_default=None)
    bytes = fields.Integer(required=False, allow_none=True, load_default=None)


class UpdateSupplierProfileSchema(Schema):
    business_name = fields.Str(required=True)
    category = fields.Str(required=False, allow_none=True, load_default=None)
    location = fields.Str(required=False, allow_none=True, load_default=None)
    description = fields.Str(required=False, allow_none=True, load_default=None)
    photo_visibility = fields.Str(required=False, allow_none=True, load_default=None)
    visible_image_source = fields.Str(required=False, allow_none=True, load_default=None)
    whatsapp_number = fields.Str(required=False, allow_none=True, load_default=None)
    # fields.Email -- same real format validation auth's own schemas
    # already use (auth_schemas.py), not a hand-rolled regex.
    contact_email = fields.Email(required=False, allow_none=True, load_default=None)
    tiktok_handle = fields.Str(required=False, allow_none=True, load_default=None)
    share_contact_details = fields.Bool(required=False, load_default=False)
    # Fulfilment terms -- see the columns' own comment in
    # supplier_profile.py. BOTH are nullable and BOTH mean something
    # real when null: offers_delivery None = "hasn't said" (never
    # "doesn't deliver"), minimum_order_cents None = "no minimum"
    # (never zero). load_default=None, not False -- defaulting a
    # tri-state to one of its answers is how the boolean version got
    # this wrong.
    offers_delivery = fields.Bool(required=False, allow_none=True, load_default=None)
    minimum_order_cents = fields.Integer(required=False, allow_none=True, load_default=None)
    # A plain bool with a False default is correct here, unlike
    # offers_delivery above -- "don't show my activity" is a real,
    # complete answer that asserts nothing on the supplier's behalf.
    # See the column's own comment in supplier_profile.py.
    show_last_active = fields.Bool(required=False, load_default=False)
    # Defaults TRUE here to match the column -- see its own comment on
    # why this one defaults on where show_last_active defaults off.
    show_track_record = fields.Bool(required=False, load_default=True)
    # The supplier's own premises -- all optional, same reasoning as
    # every other optional field here: a supplier who hasn't set this
    # up yet still has a fully working profile otherwise.
    collection_building = fields.Str(required=False, allow_none=True, load_default=None)
    collection_street = fields.Str(required=False, allow_none=True, load_default=None)
    collection_suburb = fields.Str(required=False, allow_none=True, load_default=None)
    collection_city = fields.Str(required=False, allow_none=True, load_default=None)
    collection_province = fields.Str(required=False, allow_none=True, load_default=None)
    collection_postal_code = fields.Str(required=False, allow_none=True, load_default=None)
    collection_latitude = fields.Float(required=False, allow_none=True, load_default=None)
    collection_longitude = fields.Float(required=False, allow_none=True, load_default=None)
