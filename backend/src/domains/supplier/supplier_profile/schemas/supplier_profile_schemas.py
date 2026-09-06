"""
supplier_profile's own request schemas -- shape validation only (real
business rules live in supplier_profile_service.py, same split as
every other domain's schemas/ vs services/ in this codebase).
"""
from __future__ import annotations

from marshmallow import Schema, fields


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
