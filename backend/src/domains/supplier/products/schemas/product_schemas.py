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
    selling_unit = fields.Str(required=True, validate=validate.OneOf(_UNIT_VALUES))
    unit_quantity = fields.Integer(required=False, allow_none=True, load_default=None)
    unit_measure = fields.Str(
        required=False, allow_none=True, load_default=None, validate=validate.OneOf(_UNIT_VALUES)
    )


class UpdateProductSchema(Schema):
    name = fields.Str(required=True)
    category = fields.Str(required=True, validate=validate.OneOf(_CATEGORY_VALUES))
    price_cents = fields.Integer(required=True)
    selling_unit = fields.Str(required=True, validate=validate.OneOf(_UNIT_VALUES))


class BulkAdjustPriceSchema(Schema):
    product_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    direction = fields.Str(required=True, validate=validate.OneOf(["INCREASE", "DECREASE"]))
    type = fields.Str(required=True, validate=validate.OneOf(["PERCENTAGE", "FIXED"]))
    value = fields.Integer(required=True, validate=validate.Range(min=0))


class BulkArchiveSchema(Schema):
    product_ids = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))


class RegisterMediaSchema(Schema):
    cloudinary_public_id = fields.Str(required=True)
    secure_url = fields.Str(required=True)
    resource_type = fields.Str(required=False, load_default="image")
    format = fields.Str(required=False, allow_none=True, load_default=None)
    width = fields.Integer(required=False, allow_none=True, load_default=None)
    height = fields.Integer(required=False, allow_none=True, load_default=None)
    bytes = fields.Integer(required=False, allow_none=True, load_default=None)
