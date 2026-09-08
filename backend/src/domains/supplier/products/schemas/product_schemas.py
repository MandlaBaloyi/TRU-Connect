"""
products request schemas -- shape validation only (required keys,
types, enum membership). Business rules (name length, price sanity,
ownership) stay in product_service.py, same split this codebase's
other schema files already draw (see connections' own
connections_schemas.py docstring).
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate

from src.domains.supplier.products.models.product import ProductCategory, ProductUnit

_CATEGORY_VALUES = [c.value for c in ProductCategory]
_UNIT_VALUES = [u.value for u in ProductUnit]


class CreateProductSchema(Schema):
    name = fields.Str(required=True)
    category = fields.Str(required=True, validate=validate.OneOf(_CATEGORY_VALUES))
    price_cents = fields.Integer(required=True)
    # NOT required=True -- see product.py's own compare_at_price_cents
    # docstring. A sale/promotion price a supplier sets when running
    # one; validated against price_cents in product_service.py, not
    # here (a shape schema doesn't know about a second field's value).
    compare_at_price_cents = fields.Integer(required=False, allow_none=True, load_default=None)
    selling_unit = fields.Str(required=True, validate=validate.OneOf(_UNIT_VALUES))
    unit_quantity = fields.Integer(required=False, allow_none=True, load_default=None)
    unit_measure = fields.Str(
        required=False, allow_none=True, load_default=None, validate=validate.OneOf(_UNIT_VALUES)
    )
    description = fields.Str(required=False, allow_none=True, load_default=None)
    # Optional to type -- left blank means product_service.py
    # auto-fills one via algorithms/sku_generator.py.
    # product_code is DELIBERATELY absent from this schema -- never
    # accepted from any request, always server-generated, see
    # product.py's own product_code column docstring.
    sku = fields.Str(required=False, allow_none=True, load_default=None)


class UpdateProductSchema(Schema):
    name = fields.Str(required=True)
    category = fields.Str(required=True, validate=validate.OneOf(_CATEGORY_VALUES))
    price_cents = fields.Integer(required=True)
    compare_at_price_cents = fields.Integer(required=False, allow_none=True, load_default=None)
    selling_unit = fields.Str(required=True, validate=validate.OneOf(_UNIT_VALUES))
    # WHAT IS INSIDE THE UNIT. CreateProductSchema has accepted these
    # from the beginning and this one never did, so a pack size could
    # be set at creation and then never corrected -- and since the app
    # had no field for it either, in practice it was never set at all.
    unit_quantity = fields.Integer(required=False, allow_none=True, load_default=None)
    unit_measure = fields.Str(
        required=False, allow_none=True, load_default=None, validate=validate.OneOf(_UNIT_VALUES)
    )
    description = fields.Str(required=False, allow_none=True, load_default=None)
    # None here means "leave the existing SKU alone" -- see
    # product_service.py's own update_product docstring. Still never
    # product_code, same reasoning as CreateProductSchema above.
    sku = fields.Str(required=False, allow_none=True, load_default=None)


class BulkAdjustPriceSchema(Schema):
    product_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    direction = fields.Str(required=True, validate=validate.OneOf(["INCREASE", "DECREASE"]))
    type = fields.Str(required=True, validate=validate.OneOf(["PERCENTAGE", "FIXED"]))
    value = fields.Integer(required=True, validate=validate.Range(min=0))


class BulkArchiveSchema(Schema):
    product_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))


class BulkSetDiscountSchema(Schema):
    product_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    # Whole percentage points, e.g. 20 for "20% off" -- the real
    # 1-99 bound is enforced in product_service.py (a shape schema
    # doesn't know about the division-by-zero/negative-price math that
    # makes 0 and 100+ genuinely invalid, not just unusual).
    discount_percent = fields.Integer(required=True)


class RegisterMediaSchema(Schema):
    cloudinary_public_id = fields.Str(required=True)
    secure_url = fields.Str(required=True)
    resource_type = fields.Str(required=False, load_default="image")
    format = fields.Str(required=False, allow_none=True, load_default=None)
    width = fields.Integer(required=False, allow_none=True, load_default=None)
    height = fields.Integer(required=False, allow_none=True, load_default=None)
    bytes = fields.Integer(required=False, allow_none=True, load_default=None)
